"""Génère le rapport Power BI (format PBIR) à partir des maquettes ui/.

Écrit sous ProjetTest.Report/ :
  - definition/report.json, definition/pages/**    : pages, segments et visuels
  - StaticResources/RegisteredResources/ProjetTest.json : thème (palette des maquettes)

Les pages sont entièrement régénérées : ne pas les modifier à la main, modifier ce script.
Usage : python3 scripts/generer_rapport.py
"""

import hashlib
import json
import shutil
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
RAPPORT = RACINE / "ProjetTest.Report"
DEF = RAPPORT / "definition"

S_VISUEL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json"
S_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.4.0/schema.json"
S_PAGES = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json"
S_RAPPORT = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.0.0/schema.json"

# Palette des maquettes (ui/assets/style.css)
SERIES = ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#6250D6", "#E34948"]
N1 = "#A3A19A"
SURFACE, PAGE, GRILLE = "#FCFCFB", "#F4F4F1", "#E1E0D9"
ENCRE, ENCRE2, ENCRE3 = "#0B0B0B", "#52514E", "#6F6D68"
COULEURS = {
    ("Produits", "categorie"): {"Informatique": SERIES[0], "Mobilier": SERIES[1], "Fournitures": SERIES[2], "Téléphonie": SERIES[3]},
    ("Clients", "segment"): {"Grand compte": SERIES[0], "PME": SERIES[1], "Particulier": SERIES[2]},
}

# Grille : largeur 1280, marges 16, 12 colonnes séparées de 12
L_PAGE, MARGE, GOUT = 1280, 16, 12
COL = (L_PAGE - 2 * MARGE - 11 * GOUT) / 12


def x_col(c):
    return MARGE + c * (COL + GOUT)


def l_col(n):
    return n * COL + (n - 1) * GOUT


# ---------- Expressions PBIR ----------
def lit(v):
    if isinstance(v, bool):
        valeur = "true" if v else "false"
    elif isinstance(v, int):
        valeur = f"{v}L"
    elif isinstance(v, float):
        valeur = f"{v}D"
    else:
        valeur = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": valeur}}}


def col(table, colonne):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": colonne}}


def mes(nom, table="Ventes"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": nom}}


def ref(champ):
    c = champ.get("Column") or champ.get("Measure")
    return f'{c["Expression"]["SourceRef"]["Entity"]}.{c["Property"]}'


def proj(champ, nom=None):
    p = {"field": champ, "queryRef": ref(champ), "nativeQueryRef": nom or (champ.get("Column") or champ.get("Measure"))["Property"]}
    if nom:
        p["displayName"] = nom
    return p


def couleur(hexa):
    return {"solid": {"color": lit(hexa)}}


def couleur_mesure(nom):
    return {"solid": {"color": {"expr": mes(nom)}}}


def props(**kw):
    return [{"properties": {k: (v if isinstance(v, dict) else lit(v)) for k, v in kw.items()}}]


def selecteur_valeur(champ, valeur):
    c = champ["Column"]
    return {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": champ,
                                                  "Right": {"Literal": {"Value": "'" + valeur.replace("'", "''") + "'"}}}}}]}


def couleurs_entites(champ):
    """Une couleur fixe par valeur (catégorie, segment) : la couleur suit l'entité, pas son rang."""
    c = champ["Column"]
    table = COULEURS.get((c["Expression"]["SourceRef"]["Entity"], c["Property"]), {})
    return [{"properties": {"fill": couleur(h)}, "selector": selecteur_valeur(champ, v)} for v, h in table.items()]


def conteneur(titre=None, sous_titre=None, fond=True, bordure=True):
    o = {"title": props(show=bool(titre), **({"text": titre} if titre else {}))}
    if sous_titre:
        o["subTitle"] = props(show=True, text=sous_titre)
    if not fond:
        o["background"] = props(show=False)
    if not bordure:
        o["border"] = props(show=False)
    return o


def ident(*parties):
    return hashlib.sha1("/".join(parties).encode()).hexdigest()[:20]


def filtre_top(champ, n, mesure):
    """Filtre « N premiers » tel que l'écrit Power BI Desktop : sous-requête triée et limitée."""
    c = champ["Column"]
    entite = c["Expression"]["SourceRef"]["Entity"]
    m = mesure["Measure"]
    sous_requete = {"Version": 2,
                    "From": [{"Name": "e", "Entity": entite, "Type": 0},
                             {"Name": "m", "Entity": m["Expression"]["SourceRef"]["Entity"], "Type": 0}],
                    "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "e"}}, "Property": c["Property"]}, "Name": "champ"}],
                    "OrderBy": [{"Direction": 2, "Expression": {"Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": m["Property"]}}}],
                    "Top": n}
    return {"name": ident("top", ref(champ), str(n)), "field": champ, "type": "TopN",
            "filter": {"Version": 2,
                       "From": [{"Name": "sousrequete", "Expression": {"Subquery": {"Query": sous_requete}}, "Type": 2},
                                {"Name": "e", "Entity": entite, "Type": 0}],
                       "Where": [{"Condition": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "e"}}, "Property": c["Property"]}}],
                           "Table": {"SourceRef": {"Source": "sousrequete"}}}}}]}}


def tri(champ, sens="Descending"):
    return {"sort": [{"field": champ, "direction": sens}], "isDefaultSort": True}


# ---------- Page ----------
class Page:
    def __init__(self, nom, titre):
        self.nom, self.titre, self.visuels, self.y = nom, titre, [], 0

    def ajouter(self, cle, x, y, l, h, visuel, filtres=None):
        v = {"$schema": S_VISUEL, "name": ident(self.nom, cle),
             "position": {"x": round(x, 2), "y": round(y, 2), "z": len(self.visuels) * 1000, "height": round(h, 2),
                          "width": round(l, 2), "tabOrder": len(self.visuels) * 1000},
             "visual": {**visuel, "drillFilterOtherVisuals": True}}
        if filtres:
            v["filterConfig"] = {"filters": filtres}
        self.visuels.append((cle, v))
        self.y = max(self.y, y + h)

    # --- En-tête : titre, navigation, segments ---
    def entete(self, pages):
        self.ajouter("titre", MARGE, 10, 420, 44, {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [
                {"value": self.titre, "textStyle": {"fontSize": "20pt", "fontWeight": "bold", "color": ENCRE}}]}]}}]},
            "visualContainerObjects": conteneur(fond=False, bordure=False)})
        lb, hb = 118, 34
        for i, (nom, titre) in enumerate(pages):
            actif = nom == self.nom
            self.ajouter(f"nav-{nom}", L_PAGE - MARGE - (len(pages) - i) * lb - (len(pages) - 1 - i) * 8, 14, lb, hb, {
                "visualType": "actionButton",
                "objects": {
                    "icon": [{"properties": {"show": lit(False)}, "selector": {"id": "default"}}],
                    "text": [{"properties": {"show": lit(True), "text": lit(titre), "fontColor": couleur("#FFFFFF" if actif else ENCRE2),
                                             "fontSize": lit(11.0), "bold": lit(actif)}, "selector": {"id": "default"}}],
                    "fill": [{"properties": {"show": lit(True), "fillColor": couleur(SERIES[0] if actif else SURFACE),
                                             "transparency": lit(0.0)}, "selector": {"id": "default"}}],
                    "outline": [{"properties": {"show": lit(not actif), "lineColor": couleur(GRILLE), "roundEdge": lit(8.0)},
                                 "selector": {"id": "default"}}],
                },
                "visualContainerObjects": {**conteneur(fond=False, bordure=False),
                                           "visualLink": props(show=True, type="PageNavigation", navigationSection=nom)}})

    def segments(self):
        y, h = 62, 58
        champs = [
            ("annee", col("Calendrier", "Année"), "Année", 196, {"horizontal": True, "defaut": 2025}),
            ("mois", col("Calendrier", "Mois"), "Mois", None, {}),
            ("categorie", col("Produits", "categorie"), "Catégorie", None, {}),
            ("produit", col("Produits", "nom_produit"), "Produit", None, {"recherche": True}),
            ("segment", col("Clients", "segment"), "Segment", None, {}),
            ("region", col("Clients", "region"), "Région", None, {}),
            ("ville", col("Clients", "ville"), "Ville", None, {"recherche": True}),
            ("client", col("Clients", "nom_client"), "Client", None, {"recherche": True}),
        ]
        reste = (L_PAGE - 2 * MARGE - 196 - (len(champs) - 1) * 8) / (len(champs) - 1)
        x = MARGE
        for cle, champ, titre, largeur, opt in champs:
            l = largeur or reste
            general = {"orientation": lit(1.0 if opt.get("horizontal") else 0.0)}
            if opt.get("recherche"):
                general["selfFilterEnabled"] = lit(True)
            if "defaut" in opt:
                c = champ["Column"]
                general["filter"] = {"filter": {"Version": 2, "From": [{"Name": "c", "Entity": c["Expression"]["SourceRef"]["Entity"], "Type": 0}],
                                                "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": c["Property"]}}],
                                                                                "Values": [[{"Literal": {"Value": f'{opt["defaut"]}L'}}]]}}}]}}
            self.ajouter(f"segment-{cle}", x, y, l, h, {
                "visualType": "slicer",
                "query": {"queryState": {"Values": {"projections": [proj(champ, titre)]}}},
                "objects": {"general": [{"properties": general}],
                            "data": props(mode="Basic" if opt.get("horizontal") else "Dropdown"),
                            "header": props(show=True, text=titre, fontColor=couleur(ENCRE3)),
                            "selection": props(selectAllCheckboxEnabled=not opt.get("horizontal"))},
                "visualContainerObjects": conteneur(),
                "syncGroup": {"groupName": f"segment-{cle}", "fieldChanges": True, "filterChanges": True}})
            x += l + 8

    # --- Tuiles KPI : valeur + ligne d'évolution / de contexte ---
    def kpis(self, tuiles, y=132):
        n = len(tuiles)
        l = (L_PAGE - 2 * MARGE - (n - 1) * GOUT) / n
        for i, (lib, mesure, texte, couleur_texte) in enumerate(tuiles):
            x = MARGE + i * (l + GOUT)
            self.ajouter(f"kpi-{i}", x, y, l, 70, {
                "visualType": "card",
                "query": {"queryState": {"Values": {"projections": [proj(mes(mesure))]}}},
                "objects": {"labels": props(fontSize=20.0, color=couleur(ENCRE), labelDisplayUnits=0.0),
                            "categoryLabels": props(show=False)},
                "visualContainerObjects": {**conteneur(lib, bordure=False),
                                           "title": props(show=True, text=lib, fontColor=couleur(ENCRE2), fontSize=10.0, bold=False)}})
            self.ajouter(f"kpi-{i}-texte", x, y + 70, l, 28, {
                "visualType": "card",
                "query": {"queryState": {"Values": {"projections": [proj(mes(texte))]}}},
                "objects": {"labels": props(fontSize=9.0, color=couleur_mesure(couleur_texte) if couleur_texte else couleur(ENCRE3)),
                            "categoryLabels": props(show=False)},
                "visualContainerObjects": conteneur(bordure=False)})
        return y + 98 + GOUT

    # --- Visuels ---
    def visuel(self, cle, c, y, span, h, type_, titre, sous_titre, roles, objets=None, tri_=None, filtres=None):
        v = {"visualType": type_, "query": {"queryState": {r: {"projections": p} for r, p in roles.items()}},
             "visualContainerObjects": conteneur(titre, sous_titre)}
        if tri_:
            v["query"]["sortDefinition"] = tri_
        if objets:
            v["objects"] = objets
        self.ajouter(cle, x_col(c), y, l_col(span), h, v, filtres)

    def ecrire(self, dossier):
        d = dossier / self.nom
        hauteur = int(self.y + MARGE)
        (d / "visuals").mkdir(parents=True)
        ecrire_json(d / "page.json", {"$schema": S_PAGE, "name": self.nom, "displayName": self.titre,
                                       "displayOption": "FitToWidth", "height": hauteur, "width": L_PAGE})
        for cle, v in self.visuels:
            ecrire_json(d / "visuals" / v["name"] / "visual.json", v)


def ecrire_json(chemin, donnees):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------- Raccourcis de formatage ----------
LEGENDE_HAUT = {"legend": props(show=True, position="Top")}
SANS_LEGENDE = {"legend": props(show=False)}
ETIQUETTES = {"labels": props(show=True, color=couleur(ENCRE2))}


def series_couleurs(*paires):
    return [{"properties": {"fill": couleur(h)}, "selector": {"metadata": ref(m)}} for m, h in paires]


def couleur_par_point(nom_mesure):
    return [{"properties": {"fill": couleur_mesure(nom_mesure)}, "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]


def couleur_texte_colonne(mesure_colonne, nom_couleur):
    return {"properties": {"fontColor": couleur_mesure(nom_couleur)},
            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": ref(mesure_colonne)}}


MOIS_ANNEE = col("Calendrier", "Mois-Année")
CA, CA_N1 = mes("Chiffre d'affaires"), mes("CA N-1")
EVOL = mes("Évolution CA vs N-1 (%)")


# ---------- Pages ----------
def page_overview():
    p = Page("overview", "Overview")
    y = p.kpis([
        ("Chiffre d'affaires", "Chiffre d'affaires", "Libellé évol. CA", "Couleur évol. CA"),
        ("CA cumul annuel", "CA cumul annuel", "Libellé évol. CA cumul", "Couleur évol. CA cumul"),
        ("Nombre de ventes", "Nombre de ventes", "Libellé évol. ventes", "Couleur évol. ventes"),
        ("Panier moyen", "Panier moyen", "Libellé évol. panier", "Couleur évol. panier"),
        ("Clients actifs", "Clients actifs", "Libellé évol. clients", "Couleur évol. clients"),
        ("Nouveaux clients", "Nouveaux clients", "Texte nouveaux clients", None),
        ("Taux de remise", "Taux de remise", "Texte remises", None),
    ])
    p.visuel("ca-mois", 0, y, 8, 320, "lineChart", "Chiffre d'affaires par mois",
             "Période sélectionnée comparée à la même période un an plus tôt",
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Y": [proj(CA, "Période"), proj(CA_N1, "Même période N-1")]},
             {**LEGENDE_HAUT, "dataPoint": series_couleurs((CA, SERIES[0]), (CA_N1, N1))}, tri(MOIS_ANNEE, "Ascending"))
    seg = col("Clients", "segment")
    p.visuel("ca-segment", 8, y, 4, 320, "donutChart", "CA par segment client", None,
             {"Category": [proj(seg, "Segment")], "Y": [proj(CA)]},
             {"dataPoint": couleurs_entites(seg), "legend": props(show=True, position="Bottom"),
              "labels": props(show=True, labelStyle="Percent of total")})
    y += 320 + GOUT
    for i, (cle, champ, titre) in enumerate([("ca-categorie", col("Produits", "categorie"), "CA par catégorie"),
                                              ("ca-region", col("Clients", "region"), "CA par région")]):
        p.visuel(cle, 6 * i, y, 6, 300, "clusteredBarChart", titre, "Montant du chiffre d'affaires",
                 {"Category": [proj(champ)], "Y": [proj(CA)]},
                 {**ETIQUETTES, **SANS_LEGENDE, "dataPoint": [{"properties": {"fill": couleur(SERIES[0])}}]}, tri(CA))
    y += 300 + GOUT
    for i, (cle, champs, titre, entite) in enumerate([
            ("top-produits", [col("Produits", "nom_produit"), col("Produits", "categorie")], "Top 5 produits", "Produits"),
            ("top-clients", [col("Clients", "nom_client"), col("Clients", "segment")], "Top 5 clients", "Clients")]):
        p.visuel(cle, 6 * i, y, 6, 240, "tableEx", titre, "Classés par chiffre d'affaires",
                 {"Values": [proj(champs[0]), proj(champs[1]), proj(CA, "CA"), proj(EVOL, "vs N-1")]},
                 {"values": [couleur_texte_colonne(EVOL, "Couleur évol. CA")]}, tri(CA),
                 [filtre_top(champs[0], 5, CA)])
    return p


def page_clients():
    p = Page("clients", "Clients")
    y = p.kpis([
        ("Clients actifs", "Clients actifs", "Libellé évol. clients", "Couleur évol. clients"),
        ("Taux de clients actifs", "Taux de clients actifs", "Texte portefeuille", None),
        ("Nouveaux clients", "Nouveaux clients", "Texte nouveaux", None),
        ("Taux de rétention", "Taux de rétention", "Texte rétention", None),
        ("Clients perdus", "Clients perdus", "Texte perdus", None),
        ("CA moyen par client", "CA moyen par client", "Libellé évol. CA moyen client", "Couleur évol. CA moyen client"),
        ("Fréquence d'achat", "Fréquence d'achat", "Texte fréquence", None),
        ("Part du CA des 10 premiers", "Part du CA des 10 premiers clients", "Texte concentration", None),
    ])
    actifs, nouveaux = mes("Clients actifs"), mes("Nouveaux clients")
    p.visuel("clients-mois", 0, y, 6, 300, "lineChart", "Clients actifs et nouveaux clients par mois", "Nombre de clients distincts",
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Y": [proj(actifs), proj(nouveaux)]},
             {**LEGENDE_HAUT, "dataPoint": series_couleurs((actifs, SERIES[0]), (nouveaux, SERIES[1]))}, tri(MOIS_ANNEE, "Ascending"))
    seg = col("Clients", "segment")
    p.visuel("segment-n1", 6, y, 6, 300, "clusteredBarChart", "CA par segment client", "Période comparée à N-1",
             {"Category": [proj(seg, "Segment")], "Y": [proj(CA, "Période"), proj(CA_N1, "Même période N-1")]},
             {**LEGENDE_HAUT, **ETIQUETTES, "dataPoint": series_couleurs((CA, SERIES[0]), (CA_N1, N1))}, tri(CA))
    y += 300 + GOUT
    region = col("Clients", "region")
    for i, (cle, m, titre) in enumerate([("actifs-region", actifs, "Clients actifs par région"),
                                         ("moyen-region", mes("CA moyen par client"), "CA moyen par client et par région")]):
        p.visuel(cle, 6 * i, y, 6, 300, "clusteredBarChart", titre, None,
                 {"Category": [proj(region, "Région")], "Y": [proj(m)]},
                 {**ETIQUETTES, **SANS_LEGENDE, "dataPoint": [{"properties": {"fill": couleur(SERIES[0])}}]}, tri(m))
    y += 300 + GOUT
    client = col("Clients", "nom_client")
    p.visuel("profil", 0, y, 6, 340, "scatterChart", "Profil des clients",
             "Panier moyen selon le nombre d'achats · taille = CA",
             {"Category": [proj(client, "Client")], "Series": [proj(seg, "Segment")],
              "X": [proj(mes("Nombre de ventes"), "Nombre d'achats")], "Y": [proj(mes("Panier moyen"))], "Size": [proj(CA)]},
             {**LEGENDE_HAUT, "dataPoint": couleurs_entites(seg)})
    p.visuel("top10", 6, y, 6, 340, "clusteredBarChart", "Top 10 clients", "Classés par chiffre d'affaires",
             {"Category": [proj(client, "Client")], "Y": [proj(CA)]},
             {**ETIQUETTES, **SANS_LEGENDE, "dataPoint": [{"properties": {"fill": couleur(SERIES[0])}}]}, tri(CA),
             [filtre_top(client, 10, CA)])
    y += 340 + GOUT
    p.visuel("detail-clients", 0, y, 12, 440, "tableEx", "Détail des clients",
             "Clients actifs sur la période · cliquer un en-tête pour trier",
             {"Values": [proj(mes("Rang client"), "#"), proj(client, "Client"), proj(seg, "Segment"),
                         proj(col("Clients", "ville"), "Ville"), proj(region, "Région"), proj(CA, "CA"), proj(CA_N1, "CA N-1"),
                         proj(EVOL, "Évolution"), proj(mes("Nombre de ventes"), "Ventes"), proj(mes("Panier moyen")),
                         proj(mes("Date du dernier achat"), "Dernier achat"), proj(mes("Récence (jours)"))]},
             {"values": [couleur_texte_colonne(EVOL, "Couleur évol. CA")]}, tri(CA))
    return p


def page_ventes():
    p = Page("ventes", "Ventes")
    y = p.kpis([
        ("Chiffre d'affaires", "Chiffre d'affaires", "Libellé évol. CA", "Couleur évol. CA"),
        ("Quantité vendue", "Quantité vendue", "Libellé évol. quantité", "Couleur évol. quantité"),
        ("Nombre de ventes", "Nombre de ventes", "Libellé évol. ventes", "Couleur évol. ventes"),
        ("Prix moyen de vente", "Prix moyen de vente", "Libellé évol. prix moyen", "Couleur évol. prix moyen"),
        ("Montant des remises", "Montant des remises", "Texte taux de remise", None),
        ("Produits vendus", "Nombre de produits vendus", "Texte catalogue", None),
    ])
    mm3 = mes("CA moyenne mobile 3 mois")
    p.visuel("ca-mois", 0, y, 8, 320, "lineClusteredColumnComboChart", "Chiffre d'affaires par mois",
             "Avec la moyenne mobile sur 3 mois",
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Y": [proj(CA)], "Y2": [proj(mm3, "Moyenne mobile 3 mois")]},
             {**LEGENDE_HAUT, "dataPoint": series_couleurs((CA, SERIES[0]), (mm3, SERIES[1]))}, tri(MOIS_ANNEE, "Ascending"))
    cum, cum1 = mes("CA cumul annuel"), mes("CA cumul annuel N-1")
    mois = col("Calendrier", "Mois")
    p.visuel("cumul", 8, y, 4, 320, "lineChart", "CA cumulé sur l'année", "Comparé à l'année précédente",
             {"Category": [proj(mois)], "Y": [proj(cum, "Année"), proj(cum1, "Année N-1")]},
             {**LEGENDE_HAUT, "dataPoint": series_couleurs((cum, SERIES[0]), (cum1, N1))}, tri(mois, "Ascending"))
    y += 320 + GOUT
    cat = col("Produits", "categorie")
    ecart = mes("Évolution CA vs N-1 (€)")
    p.visuel("evol-categorie", 0, y, 6, 300, "clusteredBarChart", "Évolution du CA vs N-1 par catégorie", "Écart en euros",
             {"Category": [proj(cat, "Catégorie")], "Y": [proj(ecart, "Écart vs N-1")]},
             {**ETIQUETTES, **SANS_LEGENDE, "dataPoint": couleur_par_point("Couleur écart vs N-1")}, tri(ecart))
    p.visuel("ca-categorie-mois", 6, y, 6, 300, "lineChart", "CA mensuel par catégorie", None,
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Series": [proj(cat, "Catégorie")], "Y": [proj(CA)]},
             {**LEGENDE_HAUT, "dataPoint": couleurs_entites(cat)}, tri(MOIS_ANNEE, "Ascending"))
    y += 300 + GOUT
    mom = mes("Évolution vs mois précédent (%)")
    p.visuel("evol-mois", 0, y, 12, 240, "clusteredColumnChart", "Évolution vs mois précédent", None,
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Y": [proj(mom, "vs mois précédent")]},
             {**ETIQUETTES, **SANS_LEGENDE, "dataPoint": couleur_par_point("Couleur évol. mois")}, tri(MOIS_ANNEE, "Ascending"))
    y += 240 + GOUT
    gradient = {"expr": {"FillRule": {"Input": CA, "FillRule": {"linearGradient2": {
        "min": {"color": {"Literal": {"Value": f"'{SURFACE}'"}}},
        "max": {"color": {"Literal": {"Value": f"'{SERIES[0]}'"}}},
        "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}}
    p.visuel("matrice", 0, y, 12, 560, "pivotTable", "CA par produit et par mois", "Catégories puis produits",
             {"Rows": [proj(cat, "Catégorie"), proj(col("Produits", "nom_produit"), "Produit")],
              "Columns": [proj(MOIS_ANNEE, "Mois")], "Values": [proj(CA, "CA")]},
             {"values": [{"properties": {"backColor": {"solid": {"color": gradient}}},
                          "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": ref(CA)}}]},
             tri(CA))
    y += 560 + GOUT
    p.visuel("detail-produits", 0, y, 12, 440, "tableEx", "Détail des produits", "Cliquer un en-tête pour trier",
             {"Values": [proj(mes("Rang produit"), "#"), proj(col("Produits", "nom_produit"), "Produit"), proj(cat, "Catégorie"),
                         proj(mes("Quantité vendue"), "Quantité"), proj(CA, "CA"), proj(CA_N1, "CA N-1"), proj(ecart, "Écart"),
                         proj(EVOL, "Évolution"), proj(mes("Part du CA")), proj(mes("Prix moyen de vente"), "Prix moyen"),
                         proj(mes("Taux de remise"))]},
             {"values": [couleur_texte_colonne(EVOL, "Couleur évol. CA")]}, tri(CA))
    return p


# ---------- Thème ----------
def theme():
    texte = lambda taille, c, gras=False: {"fontFace": "Segoe UI Semibold" if gras else "Segoe UI", "fontSize": taille, "color": c}
    return {
        "name": "ProjetTest",
        "dataColors": SERIES,
        "good": "#0CA30C", "neutral": "#F0EFEC", "bad": "#D03B3B",
        "maximum": SERIES[0], "center": "#86B6EF", "minimum": "#CDE2FB",
        "background": SURFACE, "foreground": ENCRE, "tableAccent": SERIES[0],
        "textClasses": {"title": texte(11, ENCRE, True), "header": texte(10, ENCRE2, True), "label": texte(10, ENCRE2),
                        "callout": texte(20, ENCRE, True)},
        "visualStyles": {
            "*": {"*": {
                "background": [{"show": True, "color": {"solid": {"color": SURFACE}}, "transparency": 0}],
                "border": [{"show": True, "color": {"solid": {"color": GRILLE}}, "radius": 10}],
                "dropShadow": [{"show": False}],
                "title": [{"show": True, "fontColor": {"solid": {"color": ENCRE}}, "fontSize": 11, "bold": True}],
                "subTitle": [{"fontColor": {"solid": {"color": ENCRE3}}, "fontSize": 9}],
                "valueAxis": [{"gridlineColor": {"solid": {"color": GRILLE}}, "gridlineStyle": "solid",
                               "labelColor": {"solid": {"color": ENCRE3}}, "showAxisTitle": False}],
                "categoryAxis": [{"labelColor": {"solid": {"color": ENCRE3}}, "showAxisTitle": False}],
                "legend": [{"labelColor": {"solid": {"color": ENCRE2}}, "fontSize": 9}],
                "lineStyles": [{"strokeWidth": 2}],
            }},
            "page": {"*": {"background": [{"color": {"solid": {"color": PAGE}}, "transparency": 0}],
                           "outspace": [{"color": {"solid": {"color": PAGE}}}]}},
            "tableEx": {"*": {"columnHeaders": [{"fontColor": {"solid": {"color": ENCRE2}}, "bold": True}],
                              "grid": [{"gridHorizontalColor": {"solid": {"color": GRILLE}}, "gridVertical": False}]}},
        },
    }


def main():
    pages = [page_overview(), page_clients(), page_ventes()]
    liste = [(p.nom, p.titre) for p in pages]
    for p in pages:
        p.entete(liste)
        p.segments()

    dossier = DEF / "pages"
    shutil.rmtree(dossier, ignore_errors=True)
    for p in pages:
        p.ecrire(dossier)
    ecrire_json(dossier / "pages.json", {"$schema": S_PAGES, "pageOrder": [p.nom for p in pages], "activePageName": pages[0].nom})

    ecrire_json(RAPPORT / "StaticResources" / "RegisteredResources" / "ProjetTest.json", theme())
    ecrire_json(DEF / "report.json", {
        "$schema": S_RAPPORT,
        "themeCollection": {
            "baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.59", "type": "SharedResources"},
            "customTheme": {"name": "ProjetTest.json", "reportVersionAtImport": "5.59", "type": "RegisteredResources"}},
        "layoutOptimization": "None",
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "ProjetTest.json", "path": "ProjetTest.json", "type": "CustomTheme"}]}],
    })
    for p in pages:
        print(f"{p.titre} : {len(p.visuels)} visuels, hauteur {int(p.y + MARGE)} px")


if __name__ == "__main__":
    main()
