# ProjetTest — Power BI (PBIP)

| Dossier | Contenu |
|---|---|
| `ProjetTest.pbip` | Point d'entrée à ouvrir dans Power BI Desktop |
| `ProjetTest.SemanticModel/` | Modèle de données (TMDL) |
| `ProjetTest.Report/` | Rapport (PBIR) |
| `sources/` | Fichiers Excel d'exemple (Produits, Clients, Ventes) et `docker-compose.yml` PostgreSQL |
| `sources/postgres/init/` | Schéma et données SQL chargés au premier démarrage de PostgreSQL |
| `scripts/` | Génération du jeu de données |
| `ui/` | Maquette HTML du rendu visé |

## Données d'exemple

Les Excel et le SQL sont générés par le même script (données identiques, graine fixe) :

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

Dans *Transformer les données > Gérer les paramètres*, régler `DossierSources`
sur le chemin du dossier `sources\` (avec la barre oblique finale).
