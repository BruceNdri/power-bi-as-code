# Catalogue des KPI

Données disponibles : `Ventes` (date, client, produit, quantité, prix unitaire facturé, montant),
`Produits` (nom, catégorie, prix catalogue), `Clients` (nom, ville, région, segment).
Période : 2024-01-01 → 2025-12-31.

## Prérequis du modèle

Les filtres Année / Mois et les comparaisons dans le temps (N-1, cumul annuel, mois précédent)
demandent une **table de dates** :

| Élément | Détail | Statut |
|---|---|---|
| Table `Calendrier` | Une ligne par jour du 2024-01-01 au 2025-12-31, marquée comme table de dates | implémenté |
| Colonnes | `Date`, `Année`, `Trimestre` (T1…T4), `Mois n°`, `Mois` (janv.…déc., trié par `Mois n°`), `Année-Mois` (2024-01…), `Début du mois`, `Mois-Année` (janv. 25…, trié par `Année-Mois n°`) | implémenté |
| Relation | `Ventes[date_vente]` → `Calendrier[Date]` (plusieurs à un) | implémenté |

Toutes les formules ci-dessous filtrent le temps via `Calendrier`, jamais via `Ventes[date_vente]`.

« Implémenté » = mesure écrite dans `ProjetTest.SemanticModel/definition/tables/Ventes.tmdl`
(dossiers d'affichage Ventes, Temps, Remises, Clients) et reproduite dans les maquettes `ui/`.
À valider à l'ouverture dans Power BI Desktop.

Formats : montants `#,0.00 €` · entiers `#,0` · taux `0.0 %` · évolutions `+0.0 %;-0.0 %;0.0 %`.

Mesures d'affichage (dossier `Affichage`) : pour les tuiles du rapport, un libellé
« ▲ +4,7 % vs N-1 » et une couleur (vert / rouge / gris) par KPI comparé à N-1, et les textes de contexte.

## Synthèse

| ID | KPI | Famille | Pages | Statut |
|---|---|---|---|---|
| V01 | Chiffre d'affaires | Ventes | Overview, Clients, Ventes | implémenté |
| V02 | Quantité vendue | Ventes | Ventes | implémenté |
| V03 | Nombre de ventes | Ventes | Overview, Ventes | implémenté |
| V04 | Panier moyen | Ventes | Overview, Clients, Ventes | implémenté |
| V05 | Prix moyen de vente | Ventes | Ventes | implémenté |
| V06 | Nombre de produits vendus | Ventes | Ventes | implémenté |
| V07 | Part du CA | Ventes | Overview, Ventes | implémenté |
| V08 | Rang produit | Ventes | Ventes | implémenté |
| T01 | CA N-1 | Temps | Overview, Clients, Ventes | implémenté |
| T02 | Évolution CA vs N-1 (€) | Temps | Ventes | implémenté |
| T03 | Évolution CA vs N-1 (%) | Temps | Overview, Clients, Ventes | implémenté |
| T04 | CA cumul annuel | Temps | Overview, Ventes | implémenté |
| T05 | CA cumul annuel N-1 | Temps | Ventes | implémenté |
| T06 | Évolution cumul annuel (%) | Temps | Overview, Ventes | implémenté |
| T07 | CA mois précédent | Temps | Ventes | implémenté |
| T08 | Évolution vs mois précédent (%) | Temps | Ventes | implémenté |
| T09 | CA moyenne mobile 3 mois | Temps | Ventes | implémenté |
| R01 | CA au prix catalogue | Remises | Ventes | implémenté |
| R02 | Montant des remises | Remises | Ventes | implémenté |
| R03 | Taux de remise | Remises | Overview, Ventes | implémenté |
| C01 | Clients actifs | Clients | Overview, Clients | implémenté |
| C02 | Clients au portefeuille | Clients | Clients | implémenté |
| C03 | Taux de clients actifs | Clients | Clients | implémenté |
| C04 | CA moyen par client | Clients | Clients | implémenté |
| C05 | Fréquence d'achat | Clients | Clients | implémenté |
| C06 | Nouveaux clients | Clients | Overview, Clients | implémenté |
| C07 | Clients actifs N-1 | Clients | Clients | implémenté |
| C08 | Évolution clients actifs (%) | Clients | Overview, Clients | implémenté |
| C09 | Taux de rétention | Clients | Clients | implémenté |
| C10 | Clients perdus | Clients | Clients | implémenté |
| C11 | Date du dernier achat | Clients | Clients | implémenté |
| C12 | Récence (jours) | Clients | Clients | implémenté |
| C13 | Part du CA des 10 premiers clients | Clients | Clients | implémenté |
| C14 | Rang client | Clients | Clients | implémenté |
| E01 | Effet volume | Explication du CA | Ventes | implémenté |
| E02 | Effet prix | Explication du CA | Ventes | implémenté |
| E03 | Effet mix produits | Explication du CA | Ventes | implémenté |
| E04 | CA des clients perdus | Explication du CA | Clients | implémenté |
| E05 | Variation du CA des clients fidèles | Explication du CA | Clients | implémenté |
| E06 | CA des clients revenus | Explication du CA | Clients | implémenté |
| E07 | CA des nouveaux clients | Explication du CA | Clients | implémenté |
| E08 | Part cumulée du CA (concentration) | Explication du CA | Clients | implémenté |

## Fiches — Ventes

### V01 · Chiffre d'affaires

- **Définition :** total facturé, remises déduites.
- **Calcul :** `SUM(Ventes[montant])`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

### V02 · Quantité vendue

- **Définition :** nombre d'unités vendues.
- **Calcul :** `SUM(Ventes[quantite])`
- **Format :** `#,0`
- **Statut :** implémenté

### V03 · Nombre de ventes

- **Définition :** nombre de lignes de vente (transactions).
- **Calcul :** `COUNTROWS(Ventes)`
- **Format :** `#,0`
- **Statut :** implémenté

### V04 · Panier moyen

- **Définition :** montant moyen d'une vente.
- **Calcul :** `DIVIDE([Chiffre d'affaires], [Nombre de ventes])`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

### V05 · Prix moyen de vente

- **Définition :** prix moyen réellement facturé par unité.
- **Calcul :** `DIVIDE([Chiffre d'affaires], [Quantité vendue])`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

### V06 · Nombre de produits vendus

- **Définition :** nombre de références différentes vendues sur la période.
- **Calcul :** `DISTINCTCOUNT(Ventes[id_produit])`
- **Format :** `#,0`
- **Statut :** implémenté

### V07 · Part du CA

- **Définition :** poids d'un élément (produit, catégorie, région, client…) dans le CA de la sélection.
- **Calcul :** `DIVIDE([Chiffre d'affaires], CALCULATE([Chiffre d'affaires], ALLSELECTED()))`
- **Format :** `0.0 %`
- **Statut :** implémenté

### V08 · Rang produit

- **Définition :** classement du produit par CA dans la sélection (1 = meilleur).
- **Calcul :** `IF(HASONEVALUE(Produits[nom_produit]), RANKX(ALLSELECTED(Produits), [Chiffre d'affaires]))`
- **Format :** `#,0`
- **Statut :** implémenté

## Fiches — Évolution dans le temps

### T01 · CA N-1

- **Définition :** CA de la même période un an plus tôt.
- **Calcul :** `CALCULATE([Chiffre d'affaires], SAMEPERIODLASTYEAR(Calendrier[Date]))`
- **Format :** `#,0.00 €`
- **Remarque :** vide pour 2024 (pas de données 2023).
- **Statut :** implémenté

### T02 · Évolution CA vs N-1 (€)

- **Calcul :** `IF(NOT ISBLANK([CA N-1]), [Chiffre d'affaires] - [CA N-1])`
- **Format :** `+#,0.00 €;-#,0.00 €;0.00 €`
- **Statut :** implémenté

### T03 · Évolution CA vs N-1 (%)

- **Calcul :** `DIVIDE([Chiffre d'affaires] - [CA N-1], [CA N-1])`
- **Format :** `+0.0 %;-0.0 %;0.0 %` — vert si positif, rouge si négatif.
- **Statut :** implémenté

### T04 · CA cumul annuel

- **Définition :** CA du 1er janvier à la date de fin de la sélection.
- **Calcul :** `TOTALYTD([Chiffre d'affaires], Calendrier[Date])`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

### T05 · CA cumul annuel N-1

- **Calcul :** `CALCULATE([CA cumul annuel], SAMEPERIODLASTYEAR(Calendrier[Date]))`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

### T06 · Évolution cumul annuel (%)

- **Calcul :** `DIVIDE([CA cumul annuel] - [CA cumul annuel N-1], [CA cumul annuel N-1])`
- **Format :** `+0.0 %;-0.0 %;0.0 %`
- **Statut :** implémenté

### T07 · CA mois précédent

- **Calcul :** `CALCULATE([Chiffre d'affaires], PREVIOUSMONTH(Calendrier[Date]))`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

### T08 · Évolution vs mois précédent (%)

- **Calcul :** `DIVIDE([Chiffre d'affaires] - [CA mois précédent], [CA mois précédent])`
- **Format :** `+0.0 %;-0.0 %;0.0 %`
- **Statut :** implémenté

### T09 · CA moyenne mobile 3 mois

- **Définition :** moyenne mensuelle du CA sur les 3 derniers mois (lisse les variations).
- **Calcul :** `DIVIDE(CALCULATE([Chiffre d'affaires], DATESINPERIOD(Calendrier[Date], MAX(Calendrier[Date]), -3, MONTH)), 3)`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

## Fiches — Remises

Le prix facturé (`Ventes[prix_unitaire]`) peut être inférieur au prix catalogue
(`Produits[prix_unitaire]`) : remises de 5 % ou 10 % accordées aux clients professionnels.

### R01 · CA au prix catalogue

- **Calcul :** `SUMX(Ventes, Ventes[quantite] * RELATED(Produits[prix_unitaire]))`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

### R02 · Montant des remises

- **Calcul :** `[CA au prix catalogue] - [Chiffre d'affaires]`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

### R03 · Taux de remise

- **Calcul :** `DIVIDE([Montant des remises], [CA au prix catalogue])`
- **Format :** `0.0 %`
- **Statut :** implémenté

## Fiches — Clients

### C01 · Clients actifs

- **Définition :** clients ayant acheté au moins une fois sur la période.
- **Calcul :** `DISTINCTCOUNT(Ventes[id_client])`
- **Format :** `#,0`
- **Statut :** implémenté

### C02 · Clients au portefeuille

- **Définition :** tous les clients connus, qu'ils aient acheté ou non.
- **Calcul :** `COUNTROWS(Clients)`
- **Format :** `#,0`
- **Statut :** implémenté

### C03 · Taux de clients actifs

- **Calcul :** `DIVIDE([Clients actifs], [Clients au portefeuille])`
- **Format :** `0.0 %`
- **Statut :** implémenté

### C04 · CA moyen par client

- **Calcul :** `DIVIDE([Chiffre d'affaires], [Clients actifs])`
- **Format :** `#,0.00 €`
- **Statut :** implémenté

### C05 · Fréquence d'achat

- **Définition :** nombre moyen d'achats par client actif.
- **Calcul :** `DIVIDE([Nombre de ventes], [Clients actifs])`
- **Format :** `#,0.0`
- **Statut :** implémenté

### C06 · Nouveaux clients

- **Définition :** clients dont le tout premier achat tombe dans la période.
- **Calcul :**
  ```dax
  VAR Debut = MIN(Calendrier[Date])
  RETURN
      COUNTROWS(
          FILTER(
              VALUES(Ventes[id_client]),
              CALCULATE(MIN(Ventes[date_vente]), REMOVEFILTERS(Calendrier)) >= Debut
          )
      )
  ```
- **Format :** `#,0`
- **Remarque :** le jeu d'exemple commence en janvier 2024, donc tous les clients sont « nouveaux » en 2024 ; en 2025, 26 clients arrivent.
- **Statut :** implémenté

### C07 · Clients actifs N-1

- **Calcul :** `CALCULATE([Clients actifs], SAMEPERIODLASTYEAR(Calendrier[Date]))`
- **Format :** `#,0`
- **Statut :** implémenté

### C08 · Évolution clients actifs (%)

- **Calcul :** `DIVIDE([Clients actifs] - [Clients actifs N-1], [Clients actifs N-1])`
- **Format :** `+0.0 %;-0.0 %;0.0 %`
- **Statut :** implémenté

### C09 · Taux de rétention

- **Définition :** part des clients actifs en N-1 qui ont de nouveau acheté sur la période.
- **Calcul :**
  ```dax
  VAR ClientsN1 = CALCULATETABLE(VALUES(Ventes[id_client]), SAMEPERIODLASTYEAR(Calendrier[Date]))
  VAR ClientsN = VALUES(Ventes[id_client])
  RETURN DIVIDE(COUNTROWS(INTERSECT(ClientsN1, ClientsN)), COUNTROWS(ClientsN1))
  ```
- **Format :** `0.0 %`
- **Statut :** implémenté

### C10 · Clients perdus

- **Définition :** clients actifs en N-1 qui n'ont pas racheté sur la période.
- **Calcul :**
  ```dax
  VAR ClientsN1 = CALCULATETABLE(VALUES(Ventes[id_client]), SAMEPERIODLASTYEAR(Calendrier[Date]))
  VAR ClientsN = VALUES(Ventes[id_client])
  RETURN COUNTROWS(EXCEPT(ClientsN1, ClientsN))
  ```
- **Format :** `#,0`
- **Statut :** implémenté

### C11 · Date du dernier achat

- **Calcul :** `MAX(Ventes[date_vente])`
- **Format :** `dd/mm/yyyy`
- **Usage :** tableau des clients.
- **Statut :** implémenté

### C12 · Récence (jours)

- **Définition :** jours écoulés entre le dernier achat du client et la fin de la période sélectionnée.
- **Calcul :** `IF(NOT ISBLANK([Date du dernier achat]), DATEDIFF([Date du dernier achat], MAX(Calendrier[Date]), DAY))`
- **Format :** `#,0`
- **Statut :** implémenté

### C13 · Part du CA des 10 premiers clients

- **Définition :** concentration du CA sur les 10 meilleurs clients de la sélection.
- **Calcul :**
  ```dax
  VAR Top10 = TOPN(10, VALUES(Clients[id_client]), [Chiffre d'affaires])
  RETURN DIVIDE(SUMX(Top10, [Chiffre d'affaires]), [Chiffre d'affaires])
  ```
- **Format :** `0.0 %`
- **Statut :** implémenté

### C14 · Rang client

- **Calcul :** `IF(HASONEVALUE(Clients[id_client]), RANKX(ALLSELECTED(Clients), [Chiffre d'affaires]))`
- **Format :** `#,0`
- **Statut :** implémenté

## Fiches — Explication du CA (v2)

Ces mesures alimentent les graphiques en cascade de la v2 : elles décomposent l'écart
`[Chiffre d'affaires] - [CA N-1]` en morceaux qui **s'additionnent exactement** à cet écart.
Implémentées dans `Ventes.tmdl` (dossier d'affichage « Explication du CA ») et reproduites dans `ui/assets/pages/*.js`.

Dans Power BI, une cascade a besoin d'une colonne d'étapes : deux tables déconnectées, `Pont prix`
(Effet volume, Effet prix, Effet mix) et `Pont clients` (Clients perdus, Clients fidèles, Clients revenus,
Nouveaux clients), avec une colonne `Ordre` pour le tri. Les mesures `Montant pont prix` et
`Montant pont clients` renvoient la valeur de l'étape (`SWITCH(SELECTEDVALUE(…[Étape]), …)`) ; la barre
« Total » de Power BI vaut l'écart de CA vs N-1, et le sous-titre (`Sous-titre pont`) rappelle les deux CA.
La cascade par catégorie (Overview) n'a pas besoin de table : catégorie en axe, `[Évolution CA vs N-1 (€)]` en valeur.

### E01 · Effet volume

- **Définition :** part de l'écart due à la variation des quantités, valorisée au prix moyen N-1.
- **Calcul :**
  ```dax
  VAR PrixN1 = DIVIDE([CA N-1], [Quantité vendue N-1])
  RETURN IF(NOT ISBLANK([CA N-1]), ([Quantité vendue] - [Quantité vendue N-1]) * PrixN1)
  ```
- **Format :** `+#,0 €;-#,0 €;0 €`
- **Statut :** implémenté

### E02 · Effet prix

- **Définition :** part de l'écart due aux prix de vente (remises comprises), produit par produit, sur les quantités de la période.
- **Calcul :** `[Chiffre d'affaires] - [CA aux prix N-1]`, avec
  ```dax
  CA aux prix N-1 =
  SUMX(VALUES(Produits[id_produit]),
      [Quantité vendue] * COALESCE(DIVIDE([CA N-1], [Quantité vendue N-1]), [Prix moyen de vente]))
  ```
  (un produit absent en N-1 est valorisé à son prix de la période : il n'a pas d'effet prix).
- **Format :** `+#,0 €;-#,0 €;0 €`
- **Statut :** implémenté

### E03 · Effet mix produits

- **Définition :** part de l'écart due au déplacement des ventes vers des produits plus chers ou moins chers.
- **Calcul :** `[CA aux prix N-1] - [Quantité vendue] * DIVIDE([CA N-1], [Quantité vendue N-1])`
- **Contrôle :** E01 + E02 + E03 = `[Chiffre d'affaires] - [CA N-1]`.
- **Format :** `+#,0 €;-#,0 €;0 €`
- **Statut :** implémenté

### E04 · CA des clients perdus

- **Définition :** CA N-1 des clients actifs en N-1 et sans achat sur la période, en négatif.
- **Calcul :**
  ```dax
  - SUMX(FILTER(VALUES(Clients[id_client]), ISBLANK([Chiffre d'affaires]) && NOT ISBLANK([CA N-1])), [CA N-1])
  ```
- **Statut :** implémenté

### E05 · Variation du CA des clients fidèles

- **Définition :** écart de CA des clients actifs sur les deux périodes.
- **Calcul :** `SUMX(FILTER(VALUES(Clients[id_client]), NOT ISBLANK([Chiffre d'affaires]) && NOT ISBLANK([CA N-1])), [Chiffre d'affaires] - [CA N-1])`
- **Statut :** implémenté

### E06 · CA des clients revenus

- **Définition :** CA des clients actifs sur la période, absents en N-1 mais déjà clients auparavant.
- **Calcul :** comme E07, avec premier achat **avant** le début de la période.
- **Statut :** implémenté

### E07 · CA des nouveaux clients

- **Définition :** CA des clients dont le premier achat (toutes périodes) tombe dans la période.
- **Calcul :**
  ```dax
  VAR Debut = MIN(Calendrier[Date])
  RETURN SUMX(
      FILTER(VALUES(Clients[id_client]),
          NOT ISBLANK([Chiffre d'affaires]) && ISBLANK([CA N-1])
          && CALCULATE(MIN(Ventes[date_vente]), ALL(Calendrier)) >= Debut),
      [Chiffre d'affaires])
  ```
- **Contrôle :** CA N-1 + E04 + E05 + E06 + E07 = `[Chiffre d'affaires]`.
- **Statut :** implémenté

### E08 · Part cumulée du CA (concentration)

- **Définition :** pour chaque client classé du plus gros au plus petit, part du CA réalisée par lui et tous ceux qui le précèdent.
  Repère affiché : part du CA des 20 % premiers clients.
- **Calcul :**
  ```dax
  VAR CAClient = [Chiffre d'affaires]
  RETURN IF(HASONEVALUE(Clients[nom_client]) && NOT ISBLANK(CAClient),
      DIVIDE(SUMX(FILTER(ALLSELECTED(Clients), [Chiffre d'affaires] >= CAClient), [Chiffre d'affaires]),
             CALCULATE([Chiffre d'affaires], ALLSELECTED(Clients))))
  ```
  Le repère des 20 % est donné par la mesure `Texte concentration 20 %` (sous-titre du graphique).
- **Format :** `0.0 %`
- **Statut :** implémenté

<!-- Modèle à copier pour un nouveau KPI

### ID · Nom du KPI

- **Définition :** ce que le KPI mesure, en une phrase métier.
- **Calcul :** formule ou DAX visé.
- **Format :**
- **Filtres / contexte :** (période, segment…)
- **Objectif / seuils :** (optionnel)
- **Statut :** à faire
-->
