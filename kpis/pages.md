# Pages du rapport

| # | Page | Objectif | Maquette | Statut |
|---|---|---|---|---|
| 1 | Overview | Vue d'ensemble de l'activité en un coup d'œil | `ui/overview.html` | rapport v1 |
| 2 | Clients | Comprendre qui achète, combien et s'ils reviennent | `ui/clients.html` | rapport v1 |
| 3 | Ventes | Analyser les ventes par produit, catégorie et dans le temps | `ui/ventes.html` | rapport v1 |

Les ID de KPI (V01, T03, C06…) renvoient à [kpis.md](kpis.md).

## Éléments communs aux 3 pages

- **En-tête :** titre de la page, période sélectionnée, navigation entre les 3 pages.
- **Panneau de filtres** (segments synchronisés sur les 3 pages) :

  | Filtre | Champ | Type |
  |---|---|---|
  | Année | `Calendrier[Année]` | boutons (Ctrl + clic pour plusieurs) — par défaut la dernière année |
  | Mois | `Calendrier[Mois]` | liste déroulante, multi-sélection |
  | Catégorie de produit | `Produits[categorie]` | liste déroulante |
  | Produit | `Produits[nom_produit]` | liste déroulante avec recherche |
  | Segment client | `Clients[segment]` | boutons |
  | Région | `Clients[region]` | liste déroulante |
  | Ville | `Clients[ville]` | liste déroulante avec recherche |
  | Client | `Clients[nom_client]` | liste déroulante avec recherche |

- **Bouton** « Réinitialiser les filtres » : dans Power BI, bouton « Rétablir les valeurs par défaut » de la barre d'outils.
- Les comparaisons N-1 sont vides si l'année sélectionnée est 2024 (pas de données 2023) :
  afficher « — » plutôt que 0.

## 1. Overview

- **Objectif :** savoir en 10 secondes si l'activité progresse, et où.
- **Public :** direction.
- **Cartes KPI (bandeau du haut) :**
  - Chiffre d'affaires (V01) avec évolution vs N-1 (T03)
  - CA cumul annuel (T04) avec évolution (T06)
  - Nombre de ventes (V03)
  - Panier moyen (V04)
  - Clients actifs (C01) avec évolution (C08)
  - Nouveaux clients (C06)
  - Taux de remise (R03)
- **Visuels :**
  - courbe : CA par mois, année N vs N-1 (axe `Calendrier[Mois]`, valeurs V01 et T01)
  - barres horizontales : CA par catégorie (V01, part V07)
  - barres : CA par région (V01)
  - anneau : CA par segment client (V07)
  - tableau : top 5 produits (nom, CA, évolution T03)
  - tableau : top 5 clients (nom, segment, CA, évolution T03)
- **Statut :** rapport v1 (généré par `scripts/generer_rapport.py`)

## 2. Clients

- **Objectif :** suivre la base clients, sa fidélité et sa valeur.
- **Public :** équipe commerciale.
- **Cartes KPI :**
  - Clients actifs (C01) avec évolution (C08)
  - Taux de clients actifs (C03)
  - Nouveaux clients (C06)
  - Taux de rétention (C09)
  - Clients perdus (C10)
  - CA moyen par client (C04)
  - Fréquence d'achat (C05)
  - Part du CA des 10 premiers clients (C13)
- **Visuels :**
  - courbe : clients actifs et nouveaux clients par mois (C01, C06)
  - barres groupées : CA par segment, période vs N-1 (V01, T01)
  - barres : clients actifs par région (C01)
  - barres : CA moyen par client par région (C04) — graphique séparé, deux mesures d'échelles différentes ne partagent jamais un axe
  - nuage de points : un point par client, fréquence d'achat (C05) × panier moyen (V04), taille = CA (V01), couleur = segment
  - barres : top 10 clients par CA (V01, C14)
  - tableau détaillé des clients : rang (C14), nom, segment, ville, région, CA (V01), CA N-1 (T01),
    évolution (T03), nombre de ventes (V03), panier moyen (V04), dernier achat (C11), récence (C12) —
    mise en forme conditionnelle sur l'évolution et la récence
- **Statut :** rapport v1 (généré par `scripts/generer_rapport.py`)

## 3. Ventes

- **Objectif :** comprendre ce qui se vend, quand, et à quel prix.
- **Public :** équipe commerciale, responsables produit.
- **Cartes KPI :**
  - Chiffre d'affaires (V01) avec évolution vs N-1 (T03)
  - Quantité vendue (V02)
  - Nombre de ventes (V03)
  - Prix moyen de vente (V05)
  - Montant des remises (R02) et taux de remise (R03)
  - Nombre de produits vendus (V06)
- **Visuels :**
  - graphique combiné : CA par mois (colonnes, V01) + moyenne mobile 3 mois (ligne, T09)
  - courbe : CA cumul annuel N vs N-1 (T04, T05)
  - barres : évolution du CA vs N-1 par catégorie (T02, T03)
  - courbes multiples : évolution mensuelle du CA par catégorie (V01, légende `Produits[categorie]`)
  - matrice : catégorie > produit en lignes, mois en colonnes, CA (V01) — mise en forme en carte de chaleur
  - tableau détaillé des produits : rang (V08), produit, catégorie, quantité (V02), CA (V01), CA N-1 (T01),
    évolution € et % (T02, T03), part du CA (V07), prix moyen (V05), taux de remise (R03)
  - barres : évolution vs mois précédent (T08) sur les 12 derniers mois
- **Statut :** rapport v1 (généré par `scripts/generer_rapport.py`)

<!-- Modèle à copier pour une nouvelle page

## N. Nom de la page

- **Objectif :** la question à laquelle la page répond.
- **Public :**
- **Cartes KPI :** (renvoyer vers kpis.md)
- **Visuels :**
  - carte : …
  - graphique : … (axe, valeur, légende)
  - tableau : …
- **Filtres / segments :** (si différents des filtres communs)
- **Maquette :** `ui/<nom-page>.html`
- **Statut :** à faire
-->
