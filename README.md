# ProjetTest — Power BI (PBIP)

| Dossier | Contenu |
|---|---|
| `ProjetTest.pbip` | Point d'entrée à ouvrir dans Power BI Desktop |
| `ProjetTest.SemanticModel/` | Modèle de données (TMDL) |
| `ProjetTest.Report/` | Rapport (PBIR), généré par `scripts/generer_rapport.py` |
| `sources/` | Fichiers Excel d'exemple (Produits, Clients, Ventes) et `docker-compose.yml` PostgreSQL |
| `sources/postgres/init/` | Schéma et données SQL chargés au premier démarrage de PostgreSQL |
| `scripts/` | Génération du jeu de données (Excel, SQL, maquettes) et du rapport PBIR |
| `kpis/` | Spécification des KPI et des pages du rapport |
| `ui/` | Maquettes HTML du rendu visé (Overview, Clients, Ventes) |

## Données d'exemple

Les Excel, le SQL et `ui/assets/donnees.js` sont générés par le même script
(données identiques, graine fixe, fichiers reproductibles à l'octet près) :

```bash
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/generer_donnees.py
```

## Base PostgreSQL

```bash
cd sources
cp .env.example .env   # puis adapter le mot de passe, l'adresse et le port
docker compose up -d
docker exec -it projet-test-postgres psql -U powerbi -d ventes
```

Les scripts de `sources/postgres/init/` ne s'exécutent qu'à la création du volume.
Pour recharger les données : `docker compose down -v && docker compose up -d`.

## Power BI Desktop

Le modèle lit PostgreSQL via deux paramètres : `ServeurPostgres` (`localhost:5433`) et `BasePostgres` (`ventes`).

1. Ouvrir le tunnel depuis le poste Windows (laisser la fenêtre ouverte) :
   ```bash
   ssh -N -L 5433:localhost:5433 <utilisateur>@<serveur>
   ```
2. Ouvrir `ProjetTest.pbip`, puis **Actualiser**.
3. À la demande d'identifiants : onglet **Base de données**, utilisateur `powerbi`,
   mot de passe dans `sources/.env`.
4. Le serveur n'a pas de SSL (le tunnel chiffre déjà le trafic) : accepter la connexion non chiffrée
   quand Power BI la propose.

Les pages du rapport sont générées : pour les modifier durablement, changer
`scripts/generer_rapport.py` puis relancer `python3 scripts/generer_rapport.py`
(Power BI Desktop fermé). Les modifications faites dans Desktop seront écrasées à la prochaine génération.

## Maquettes HTML (`ui/`)

Ouvrir `ui/index.html` dans un navigateur (aucun serveur ni dépendance).
Les 3 pages partagent les filtres (année, mois, catégorie, produit, segment, région, ville, client),
recalculent les KPI comme les mesures DAX et proposent une vue tableau pour chaque graphique.

| Fichier | Rôle |
|---|---|
| `ui/assets/app.js` | Données, filtres, calcul des KPI, structure des pages |
| `ui/assets/charts.js` | Graphiques SVG (séries temporelles, barres, anneau, nuage, tableaux, matrice) |
| `ui/assets/style.css` | Thème clair / sombre |
| `ui/assets/donnees.js` | Données générées — ne pas modifier à la main |
