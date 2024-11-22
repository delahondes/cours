#!/bin/env python3

from scitq.workflow import Workflow, URI
from scitq.fetch import list_content, check_uri
from scitq.bio.genetics import ena_get_samples, sra_get_samples, uri_get_samples, \
    find_library_layout, user_friendly_depth, filter_by, filter_by_layout
import typer
import requests
import os
import subprocess
import io
import csv
from typing import Optional
from argparse import Namespace


DEFAULT_PROVIDER = 'auto'
DEFAULT_REGIONS = 'auto'
SEED = 42
RESOURCE_BASE = 's3://scitq/resource'
RESULTS_BASE = 's3://scitq/results/metaphlan4'
#FLAVOR = 'auto:cpu>=8:ram>=120:disk>=400'
FLAVOR = 'r3-32'

def count(items, ending):
    """Count how many items end with ending"""
    return len([item for item in items if item.endswith(ending)])

def metaphlan(bioproject:str, depth:str='10M', provider:str=DEFAULT_PROVIDER,
              region:Optional[str]=DEFAULT_REGIONS, scitq_project:Optional[str]=None,
              sra:bool=False, max_workflow_workers:int=10,
              debug:bool=False, use_cache:bool=True, resource_base:str=RESOURCE_BASE,
              results_base:str=RESULTS_BASE, download_locally:bool=False,
              limit:Optional[int]=None
              ):
    """
    --depth can be 2x10M or 1x20M or just a plain number,
    it defaults to 10M with the analysis layout (paired/unpaired) guessed from the samples layout

    --provider can be either azure or ovh

    --region should stay as auto unless in very specific cases

    --scitq-project is the name of the computational batch of scitq it defaults to f'metaphlan4-{bioproject}'
    (if bioproject string contains some URI like pattern like s3://... only the last folder of the URI is retained)

    --output is a scitq URI and default to f'azure://rnd/results/metaphlan4/{bioproject}' but you can specify otherwise
    (with bioproject string filtered as for --scitq-project)

    --limit limit the number of sample within the bioproject
   
    by default the script uses the ENA but --sra option means to use the SRA
    """
    paired = None
    depth_string = depth
    depth, paired = user_friendly_depth(depth_string).to_tuple()




    ######################################################
    #                                                    #
    #    Collecting samples                              #
    #                                                    #
    ######################################################
    print('Getting samples')
    if '://' in bioproject:
        samples = uri_get_samples(bioproject)
    else:
        samples = (sra_get_samples if sra else ena_get_samples)(bioproject=bioproject)
        samples = filter_by(samples, library_strategy='WGS')
    if paired is None:
        paired = find_library_layout(samples)=='PAIRED'
    print('Filtering')
    samples = filter_by_layout(samples, paired=paired)


    ######################################################
    #                                                    #
    #    Analytical Workflow                             #
    #                                                    #
    ######################################################
    print('Starting workflow'+' in debug mode' if debug else '')
    if scitq_project is None:
        scitq_project = f'metaphlan4-{bioproject}'

    results_base = URI(results_base) / scitq_project
    resource_base = URI(resource_base)
    

    wf = Workflow(name=scitq_project, shell=True, 
                max_step_workers=5, retry=5, flavor=FLAVOR, 
                provider=provider, region=region,
                max_workflow_workers=max_workflow_workers,
                debug=debug, use_cache=use_cache)

    for sample,runs in samples.items() if limit is None else list(samples.items())[:limit]:
        print('.',end='')
        current_results_folder = results_base / sample

        # cleaning step
        step1 = wf.step(
            batch='fastp',
            name=f'fastp:{sample}',
            command=f'''zcat /input/*1.f*q.gz > /tmp/read1.fastq &
                zcat /input/*2.f*q.gz > /tmp/read2.fastq &
                wait
                fastp \
                --adapter_sequence AGATCGGAAGAGCACACGTCTGAACTCCAGTCA --adapter_sequence_r2 AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT \
                --cut_front --cut_tail --n_base_limit 0 --length_required 60 --in1 /tmp/read1.fastq --in2 /tmp/read2.fastq \
                --json /output/{sample}_fastp.json -z 1 --out1 /output/{sample}.1.fastq.gz --out2 /output/{sample}.2.fastq.gz'''\
            if paired else f'zcat /input/*.f*q.gz|fastp \
                --adapter_sequence AGATCGGAAGAGCACACGTCTGAACTCCAGTCA --adapter_sequence_r2 AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT \
                --cut_front --cut_tail --n_base_limit 0 --length_required 60 --stdin \
                --json /output/{sample}_fastp.json -z 1 -o /output/{sample}.fastq.gz',
            container='staphb/fastp:0.23.4',
            concurrency=6,
            prefetch=3,
            input=[run.uri for run in runs],
            output=current_results_folder / 'fastp',
        )

        # human filtering step (removing human DNA for ethical reasons)
        step2 = wf.step(
            batch='humanfiltering',
            name=f'bowtiehuman:{sample}',
            command=f'bowtie2 -p $CPU --mm -x /resource/chm13v2.0/chm13v2.0 -1 /input/{sample}.1.fastq.gz -2 /input/{sample}.2.fastq.gz --reorder\
    |samtools fastq -@ 2 -f 12 -F 256 -1 /output/{sample}.1.fastq -2 /output/{sample}.2.fastq -0 /dev/null -s /dev/null'\
            if paired else \
                    f'bowtie2 -p $CPU --mm -x /resource/chm13v2.0/chm13v2.0 -U /input/{sample}.fastq.gz  --reorder\
    |samtools fastq -@ 2 -f 4 -F 256 -0 /output/{sample}.fastq -s /dev/null',
            container='staphb/bowtie2:2.5.1',
            concurrency=6,
            required_tasks=step1,
            input=step1.output,
            output=current_results_folder / 'humanfiltering',
            resource=resource_base / 'chm13v2.0.tgz' + '|untar',
        )

        if depth is not None:
            # normalization step
            step3 = wf.step(
                batch='seqtk',
                name=f'seqtk:{sample}',
                command=f'''seqtk sample -s{SEED} - {depth} < /input/{sample}.1.fastq > /output/{sample}.1.fastq &
                    seqtk sample -s{SEED} - {depth} < /input/{sample}.2.fastq > /output/{sample}.2.fastq &
                    wait''' \
                if paired else \
                        f'seqtk sample -s{SEED} - {depth} < /input/{sample}.fastq > /output/{sample}.fastq',
                container='staphb/seqtk:1.3',
                concurrency=2,
                required_tasks=step2,
                input=step2.output,
                output=current_results_folder / 'seqtk',
            )

        # alignment step (metaphlan)
        step4 = wf.step(
            batch='metaphlan',
            name=f'metaphlan:{sample}',
            command=f'cat /input/*.fastq |metaphlan --input_type fastq \
                --no_map --offline --bowtie2db /resource/metaphlan/bowtie2 \
                --nproc $CPU -o /output/{sample}.metaphlan4_profile.txt',
            container='gmtscience/metaphlan4:4.1',
            concurrency=2,
            required_tasks=step2 if depth is None else step3,
            input=step2.output if depth is None else step3.output,
            output=current_results_folder / 'metaphlan',
            resource=resource_base / 'metaphlan4.1.tgz' + '|untar',
        )

    # final collection step
    step6 = wf.step(
        batch='compile',
        name='compile',
        shell=True,
        command=f'''cd /input && merge_metaphlan_tables.py *profile.txt > /output/merged_abundance_table.tsv''',
        container='gmtscience/metaphlan4:4.1',
        concurrency=1,
        required_tasks=step4.gather(),
        input=step4.gather('output'),
        output=results_base / 'compile',
    )


    ######################################################
    #                                                    #
    #    Monitoring and post-treatment                   #
    #                                                    #
    ######################################################
    print()
    wf.run(refresh=10)
    print(f'All done! Results are in {step6.output} !')

    if download_locally:
        os.makedirs(bioproject,exist_ok=True)
        step6.download(destination=os.path.join(os.getcwd(),bioproject)+'/')
        #wf.clean()




if __name__=='__main__':
    typer.run(metaphlan)