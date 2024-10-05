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

Note: se compile avec `reveal-md pipelines_cours_slides.md` après avoir installé reaveal-md: `npm install -g reveal-md`
---
## Pourquoi
----
### Préparation du traitement des données brutes

- reads de qualité faible
- retrait des séquences adaptatrices
- retrait de l'ADN de l'hôte
- normalisation de l'échantillon

⚠️ ces étapes sont dépendentes du contexte scientifique <!-- .element: class="r-fit-text" -->
----
#### Nettoyage de base des reads

- qualité Q (Phred) minimale (par défaut Q15) `$$ Q = -10 \ log _{10}(P) $$` 
    - Q|probabilité d'erreur
--|--
10|1/10
20|1/100
30|1/1000
<!-- .element: style="font-size:0.6em;" -->
- retrait des séquence adaptatrices (Illumina, Proton, _etc._)
- généralement `fastp` mais possible également `trimmomatic`

<!-- .element: style="font-size:0.8em;" -->
----
#### Retrait de l'ADN de l'hôte

- les aligneurs (`bowtie2`<!-- .element: style="font-size:0.6em;" --> ou `bwa`<!-- .element: style="font-size:0.6em;" -->) sont basés sur un algorithme `blast`<!-- .element: style="font-size:0.6em;" --> qui accepte des imperfections,
- il faut retirer les signaux dont on anticipe la présence et dont la détection n'est pas souhaitable

⇒ Utiliser une référence qui ne contient pas le génome de l'hôte est insuffisant.
----
#### Normalisation

- Le séquençage NGS est redondant et partiel
- La séquence d'un échantillon est constitué de `reads`:
  - chaque `run`, c.a.d. une itération d'un séquenceur sur une bibliothèque apporte un certain nombre de `reads` (une courte séquence de 100 à 300pb) difficile à anticiper
- La stratégie de séquençage typique est de viser une quantité de reads moyenne par échantillon 
