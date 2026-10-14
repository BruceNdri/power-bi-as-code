"""Génère le jeu de données d'exemple (ventes, produits, clients).

Les mêmes données sont écrites à deux endroits pour rester cohérentes :
  - sources/*.xlsx                      : sources Excel lues par Power Query
  - sources/postgres/init/02_donnees.sql : chargement de la base PostgreSQL
  - ui/assets/donnees.js                : données des maquettes HTML

Usage : .venv/bin/python scripts/generer_donnees.py
"""

import io
import json
import random
import re
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_SOURCES = RACINE / "sources"
FICHIER_SQL = DOSSIER_SOURCES / "postgres" / "init" / "02_donnees.sql"
FICHIER_JS = RACINE / "ui" / "assets" / "donnees.js"

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

    nb_jours = (DATE_FIN - DATE_DEBUT).days
    clients, noms_pris = [], set()
    for i in range(1, NB_CLIENTS + 1):
        ville, region = rng.choice(VILLES)
        segment = rng.choices([s for s, _ in SEGMENTS], weights=[p for _, p in SEGMENTS])[0]
        nom = None
        while nom is None or nom in noms_pris:
            nom = f"{rng.choice(NOMS)} {rng.choice(NOMS)}" if segment == "Particulier" \
                else f"{rng.choice(PREFIXES)} {rng.choice(NOMS)}"
        noms_pris.add(nom)
        # Fenêtre d'activité : arrivées étalées dans le temps, une partie des clients cesse d'acheter.
        debut = 0 if i <= 15 else rng.randint(0, 90) if rng.random() < 0.55 else rng.randint(91, nb_jours - 60)
        fin = rng.randint(min(debut + 120, nb_jours), nb_jours) if rng.random() < 0.2 else nb_jours
        clients.append({"id_client": i, "nom_client": nom, "ville": ville,
                        "region": region, "segment": segment, "_debut": debut, "_fin": fin})

    poids_segment = {"Grand compte": 3, "PME": 2, "Particulier": 1}
    poids_mois = [0.8, 0.85, 1.0, 1.0, 1.05, 0.95, 0.7, 0.6, 1.15, 1.1, 1.2, 1.4]  # saisonnalité
    jours = list(range(nb_jours + 1))
    poids_jours = [poids_mois[(DATE_DEBUT + timedelta(days=j)).month - 1] *
                   (1 + 0.12 * j / nb_jours) for j in jours]  # légère croissance
    ventes = []
    for i in range(1, NB_VENTES + 1):
        jour = rng.choices(jours, weights=poids_jours)[0]
        actifs = [c for c in clients if c["_debut"] <= jour <= c["_fin"]]
        client = rng.choices(actifs, weights=[poids_segment[c["segment"]] for c in actifs])[0]
        produit = rng.choice(produits)
        quantite = rng.randint(1, 20 if produit["prix_unitaire"] < 20 else 5)
        remise = rng.choice([0, 0, 0, 0.05, 0.10]) if client["segment"] != "Particulier" else 0
        prix = round(produit["prix_unitaire"] * (1 - remise), 2)
        ventes.append({"id_vente": i,
                       "date_vente": DATE_DEBUT + timedelta(days=jour),
                       "id_client": client["id_client"], "id_produit": produit["id_produit"],
                       "quantite": quantite, "prix_unitaire": prix,
                       "montant": round(prix * quantite, 2)})
    for c in clients:
        del c["_debut"], c["_fin"]
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
    classeur.properties.created = datetime(2026, 1, 1)
    chemin = DOSSIER_SOURCES / f"{nom}.xlsx"
    classeur.save(chemin)
    figer_horodatage(chemin)


def figer_horodatage(chemin):
    """Fixe les dates internes du .xlsx pour qu'il reste identique d'une génération à l'autre."""
    tampon = io.BytesIO()
    with zipfile.ZipFile(chemin) as source, zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as cible:
        for entree in source.infolist():
            contenu = source.read(entree.filename)
            if entree.filename == "docProps/core.xml":
                contenu = re.sub(rb"(<dcterms:modified[^>]*>)[^<]*", rb"\g<1>2026-01-01T00:00:00Z", contenu)
            cible.writestr(zipfile.ZipInfo(entree.filename, (2026, 1, 1, 0, 0, 0)), contenu, zipfile.ZIP_DEFLATED)
    chemin.write_bytes(tampon.getvalue())


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


def ecrire_js(donnees):
    tables = {nom.lower(): [[v.isoformat() if isinstance(v, date) else v for v in ligne.values()]
                            for ligne in lignes]
              for nom, lignes in donnees.items()}
    tables["colonnes"] = {nom.lower(): list(lignes[0]) for nom, lignes in donnees.items()}
    FICHIER_JS.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_JS.write_text("// Fichier généré par scripts/generer_donnees.py : ne pas modifier à la main.\n"
                          "window.DONNEES = " + json.dumps(tables, ensure_ascii=False, separators=(",", ":")) + ";\n",
                          encoding="utf-8")


def main():
    donnees = generer()
    DOSSIER_SOURCES.mkdir(exist_ok=True)
    for nom, lignes in donnees.items():
        ecrire_excel(nom, lignes)
        print(f"sources/{nom}.xlsx : {len(lignes)} lignes")
    ecrire_sql(donnees)
    print(f"{FICHIER_SQL.relative_to(RACINE)} écrit")
    ecrire_js(donnees)
    print(f"{FICHIER_JS.relative_to(RACINE)} écrit")


if __name__ == "__main__":
    main()
