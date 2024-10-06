---
title: Workflow en métagénomique
theme: dracula
revealOptions:
  transition: 'fade'
---
### Workflow en métagénomique

- Pourquoi
- Comment
- Thème du TD

Source: https://github.com/delahondes/cours/tree/main/2024-2025/pipelines
Note: se compile avec `reveal-md pipelines_cours_slides.md` après avoir installé reaveal-md: `npm install -g reveal-md`
---
## Pourquoi
### Les raisons biologiques
----
### Préparation du traitement des données brutes

- reads de qualité faible
- retrait des séquences adaptatrices
- retrait de l'ADN de l'hôte
- normalisation de l'échantillon

⚠️ ces étapes sont dépendantes du contexte scientifique <!-- .element: class="r-fit-text" -->
----
#### Nettoyage de base des reads

- qualité Q (Phred) minimale (par défaut Q15) `$$ Q = -10 \ log _{10}(P) $$` 
    - Q|probabilité d'erreur
--|--
10|1/10
20|1/100
30|1/1000
<!-- .element: style="font-size:0.6em;" -->
- retrait des séquences adaptatrices (Illumina, Proton, _etc._)
- généralement `fastp` mais possible également `trimmomatic`
- lien pour les séquences adapteur à retirer (merci MetaGenoPolis) : \
http://tiny.cc/o20pzz

<!-- .element: style="font-size:0.8em;" -->

Note: lien long pour les adapteurs: https://forgemia.inra.fr/metagenopolis/benchmark_mock/-/blob/a429a3724d4593f35b8d7323b20252a6be90e1cd/preprocessing/alientrimmer_contaminants.tfa
----
#### Retrait de l'ADN de l'hôte

- les aligneurs (`bowtie2`<!-- .element: style="font-size:0.6em;" --> ou `bwa`<!-- .element: style="font-size:0.6em;" -->) sont basés sur un algorithme `blast`<!-- .element: style="font-size:0.6em;" --> qui accepte des alignements partiels,
- il faut retirer les signaux (bruit) dont on anticipe la présence et dont la détection n'est pas souhaitable

⇒ Utiliser un aligneur avec une référence qui ne contient pas les génomes du « bruit » est insuffisant.
----
#### Normalisation

- Le séquençage NGS est redondant et partiel
- La séquence d'un échantillon est constituée de `reads`:
  - chaque `run`, c.a.d. une itération d'un séquenceur sur une bibliothèque apporte un nombre variable de `reads` (une courte séquence de 100 à 300pb)
  - La stratégie de séquençage typique est de viser une quantité de reads moyenne par échantillon 
  - ⇒ la quantité de reads par échantillon est variable
- Quelle stratégie de normalisation adopter ?

<!-- .element: style="font-size:0.8em;" -->
----
#### Normalisation: pas de stratégie universelle

- La détection des espèces (présence/absence):
  - rarefaction
- La balance entre deux espèces:
  - pas de normalisation: il faut séquencer idéalement jusqu'à obtenir du signal 
- En contexte général d'analyse d'abondance relative différentielle:
  - rarefaction
  - utilisation de statistiques _ad hoc_ (Aitchison ?) sans normalisation

<!-- .element: style="font-size:0.8em;" -->
---
## Pourquoi
### Les raisons techniques
----
#### Un calcul coûteux

- Le signal brut pèse lourd (1 à 10 Go par échantillon)
  - coût de transport (bande passante),
  - coût de stockage (bande passante de disque (IO), capacité de disque),
- Les étapes de traitement sont coûteuses en mémoire (rarefaction) et/ou en temps de calcul
- Une fois l'abondance relative obtenue (ou une autre mesure « primaire »), les traitements groupés en local sont performants.

<!-- .element: style="font-size:0.8em;" -->
----
#### Une logistique fastidieuse

- De nombreuses étapes ont un taux d'échec important:
  - Le téléchargement peut facilement échouer: télécharger en un endroit un grand nombre d'échantillons est difficile,
  - Les autres étapes sont moins délicates, mais sont toutes interdépendantes.
- Retarder le plus possible la concentration des données
----
#### La problématique du HPC

HPC: high performance computing

- Les clusters de calcul (type Jean Zay): 
  - une solution luxueuse encore très répandue dans le domaine académique
  - L'outil de référence: `SLURM`
  - Une problématique très complexe: les bottlenecks
- Les task queues en cloud: une solution très légère... dépendante du cloud ($)
  - la solution des biotechs
  - Les outils: on en parle juste après
  - Une problématique beaucoup plus simple: trouver la bonne VM
- Les solutions hybrides:
  - les clusters de calcul à débordement cloud,
  - les task queues hybrides (Kubernetes/autres)

<!-- .element: style="font-size:0.7em;" -->
----
#### Les task queues en cloud

- Une solution d'avenir
  - légèreté (problème moins complexe)
  - écologique (meilleur partage des ressources)
- Des milliers d'outils:
  - Big Data Processing: Apache: Hadoop, Spark, Flink
  - Cloud HPC: Amazon Lambda, Google Cloud Dataflow, Azure Databricks
  - Workflow: Apache Airflow, Luigi (Spotify), Celery
----
#### La bioinformatique serait-elle spécifique ?

- Les solutions précédentes sont rarement utilisées
- Une raison technique:
  - le « big data » est souvent un grand nombre de petites tâches
  - la bioinformatique est souvent un petit nombre de grosses tâches
- Une raison organisationnelle:
  - dans la plupart des industries, les traitements sont:
    - ou très standard (« off the shelf »), à la charge d'un fournisseur,
    - ou complètement spécifique (distribution d'algorithme interne)
  - en bioinfo:
    - beaucoup de semi-standard très paramétré
    - le coût d'intégration devient prépondérant
    - on aime bien partager ses solutions

<!-- .element: style="font-size:0.7em;" -->
---
## Comment ?
----
#### Les outils de bioinformatique

- Galaxy
- Snakemake
- Nextflow
- ... autres?