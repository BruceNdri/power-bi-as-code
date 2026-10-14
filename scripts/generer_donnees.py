"""Génère le jeu de données d'exemple (ventes, produits, clients).

Les mêmes données sont écrites à deux endroits pour rester cohérentes :
  - sources/*.xlsx                      : sources Excel lues par Power Query
  - sources/postgres/init/02_donnees.sql : chargement de la base PostgreSQL

Usage : .venv/bin/python scripts/generer_donnees.py
"""

import random
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_SOURCES = RACINE / "sources"
FICHIER_SQL = DOSSIER_SOURCES / "postgres" / "init" / "02_donnees.sql"

GRAINE = 42
NB_CLIENTS = 120
NB_VENTES = 3000
DATE_DEBUT = date(2024, 1, 1)
DATE_FIN = date(2025, 12, 31)

CATALOGUE = {
    "Informatique": [("Ordinateur portable", 899.00), ("Écran 27 pouces", 249.90), ("Clavier mécanique", 89.90),
                     ("Souris sans fil", 29.90), ("Station d'accueil", 159.00)],
    "Mobilier": [("Bureau assis-debout", 449.00), ("Chaise ergonomique", 329.00), ("Caisson mobile", 119.00),
                 ("Lampe de bureau", 49.90)],
    "Fournitures": [("Ramette papier A4", 5.90), ("Stylos (lot de 10)", 7.50), ("Classeurs (lot de 5)", 12.90),
                    ("Carnet de notes", 4.20), ("Agrafeuse", 14.90)],
    "Téléphonie": [("Smartphone", 599.00), ("Casque Bluetooth", 129.00), ("Chargeur rapide", 24.90)],
}

VILLES = [("Paris", "Île-de-France"), ("Versailles", "Île-de-France"), ("Lyon", "Auvergne-Rhône-Alpes"),
          ("Grenoble", "Auvergne-Rhône-Alpes"), ("Marseille", "Provence-Alpes-Côte d'Azur"),
          ("Nice", "Provence-Alpes-Côte d'Azur"), ("Toulouse", "Occitanie"), ("Montpellier", "Occitanie"),
          ("Bordeaux", "Nouvelle-Aquitaine"), ("Nantes", "Pays de la Loire"), ("Lille", "Hauts-de-France"),
          ("Strasbourg", "Grand Est"), ("Rennes", "Bretagne")]
SEGMENTS = [("Grand compte", 1), ("PME", 3), ("Particulier", 4)]
PREFIXES = ["Atelier", "Groupe", "Société", "Cabinet", "Maison", "Studio", "Comptoir"]
NOMS = ["Martin", "Bernard", "Dubois", "Durand", "Lefebvre", "Moreau", "Laurent", "Simon", "Michel", "Garcia",
        "Roux", "Fournier", "Girard", "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau", "Vincent", "Muller"]


def generer():
    rng = random.Random(GRAINE)

    produits = []
    for categorie, articles in CATALOGUE.items():
        for nom, prix in articles:
            produits.append({"id_produit": len(produits) + 1, "nom_produit": nom,
                             "categorie": categorie, "prix_unitaire": prix})

    clients = []
    for i in range(1, NB_CLIENTS + 1):
        ville, region = rng.choice(VILLES)
        segment = rng.choices([s for s, _ in SEGMENTS], weights=[p for _, p in SEGMENTS])[0]
        nom = f"{rng.choice(NOMS)} {rng.choice(NOMS)}" if segment == "Particulier" \
            else f"{rng.choice(PREFIXES)} {rng.choice(NOMS)}"
        clients.append({"id_client": i, "nom_client": nom, "ville": ville,
                        "region": region, "segment": segment})

    nb_jours = (DATE_FIN - DATE_DEBUT).days
    ventes = []
    for i in range(1, NB_VENTES + 1):
        produit = rng.choice(produits)
        client = rng.choice(clients)
        quantite = rng.randint(1, 20 if produit["prix_unitaire"] < 20 else 5)
        remise = rng.choice([0, 0, 0, 0.05, 0.10]) if client["segment"] != "Particulier" else 0
        prix = round(produit["prix_unitaire"] * (1 - remise), 2)
        ventes.append({"id_vente": i,
                       "date_vente": DATE_DEBUT + timedelta(days=rng.randint(0, nb_jours)),
                       "id_client": client["id_client"], "id_produit": produit["id_produit"],
                       "quantite": quantite, "prix_unitaire": prix,
                       "montant": round(prix * quantite, 2)})
    ventes.sort(key=lambda v: (v["date_vente"], v["id_vente"]))

    return {"Produits": produits, "Clients": clients, "Ventes": ventes}


def ecrire_excel(nom, lignes):
    classeur = Workbook()
    feuille = classeur.active
    feuille.title = nom
    colonnes = list(lignes[0])
    feuille.append(colonnes)
    for ligne in lignes:
        feuille.append([ligne[c] for c in colonnes])
    for cellule in feuille["B"] if nom == "Ventes" else []:
        cellule.number_format = "dd/mm/yyyy"
    for i, colonne in enumerate(colonnes, start=1):
        feuille.column_dimensions[feuille.cell(1, i).column_letter].width = max(12, len(colonne) + 4)
    tableau = Table(displayName=f"t{nom}", ref=feuille.dimensions)
    tableau.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    feuille.add_table(tableau)
    classeur.save(DOSSIER_SOURCES / f"{nom}.xlsx")


def sql_valeur(valeur):
    if isinstance(valeur, str):
        return "'" + valeur.replace("'", "''") + "'"
    if isinstance(valeur, date):
        return f"'{valeur.isoformat()}'"
    return str(valeur)


def ecrire_sql(donnees):
    lignes = ["-- Fichier généré par scripts/generer_donnees.py : ne pas modifier à la main.", ""]
    for nom in ("Produits", "Clients", "Ventes"):
        colonnes = list(donnees[nom][0])
        lignes.append(f"INSERT INTO {nom.lower()} ({', '.join(colonnes)}) VALUES")
        valeurs = [f"  ({', '.join(sql_valeur(l[c]) for c in colonnes)})" for l in donnees[nom]]
        lignes.append(",\n".join(valeurs) + ";")
        lignes.append("")
    FICHIER_SQL.write_text("\n".join(lignes), encoding="utf-8")


def main():
    donnees = generer()
    DOSSIER_SOURCES.mkdir(exist_ok=True)
    for nom, lignes in donnees.items():
        ecrire_excel(nom, lignes)
        print(f"sources/{nom}.xlsx : {len(lignes)} lignes")
    ecrire_sql(donnees)
    print(f"{FICHIER_SQL.relative_to(RACINE)} écrit")


if __name__ == "__main__":
    main()
