"""Génère le rapport Power BI v2 (format PBIR) à partir des maquettes ui/v2/ : thème bleu marine.

Écrit ProjetTestV2.pbip et ProjetTestV2.Report/, branché sur le même modèle que la v1
(../ProjetTest.SemanticModel). Réutilise les fonctions d'expression PBIR de generer_rapport.py.

Disposition : barre latérale marine (marque, navigation, segments), bandeau de titre, tuiles KPI,
puis une grille de 12 colonnes. Les pages sont entièrement régénérées : ne pas les modifier à la main.
Usage : python3 scripts/generer_rapport_v2.py
"""

import shutil

import generer_rapport as g
from generer_rapport import col, couleur, couleur_mesure, ecrire_json, filtre_top, ident, lit, mes, proj, props, ref, tri

RACINE = g.RACINE
RAPPORT = RACINE / "ProjetTestV2.Report"
DEF = RAPPORT / "definition"

# ---------- Charte (ui/v2/v2.css) ----------
MARINE, MARINE_2, CIEL = "#003781", "#002A63", "#13A0D3"
PAGE_FOND, SURFACE, SURFACE_2 = "#F2F5F9", "#FFFFFF", "#F5F8FC"
ENCRE, ENCRE2, ENCRE3 = "#0B1F3A", "#3D4F66", "#64758C"
GRILLE, BORD = "#E6EBF2", "#E3E9F1"
SERIES = ["#0F5BD8", "#13A0D3", "#F28C28", "#2BB39B", "#E87BA4", "#008300", "#6250D6", "#E34948"]
PRIMAIRE, N1 = MARINE, "#A7B6CB"
BON, MAUVAIS = "#1E9E57", "#D93838"
NAV_TEXTE = "#D6E2F3"
# Power BI attend une pile de polices CSS complète : un nom seul (« Segoe UI Bold ») retombe sur une police à empattements.
POLICE_GRAS = "'Segoe UI Bold', wf_segoe-ui_bold, helvetica, arial, sans-serif"
COULEURS = {
    ("Produits", "categorie"): {"Informatique": SERIES[0], "Mobilier": SERIES[1], "Fournitures": SERIES[2], "Téléphonie": SERIES[3]},
    ("Clients", "segment"): {"Grand compte": SERIES[0], "PME": SERIES[1], "Particulier": SERIES[2]},
}

# ---------- Grille ----------
L_PAGE = 1440
LARGEUR_NAV = 256
X0, MARGE, GOUT = LARGEUR_NAV + 24, 24, 16
L_MAIN = L_PAGE - X0 - MARGE
COL = (L_MAIN - 11 * GOUT) / 12


def x_col(c):
    return X0 + c * (COL + GOUT)


def l_col(n):
    return n * COL + (n - 1) * GOUT


def texte(paragraphes):
    """Zone de texte : liste de paragraphes, chacun liste de (texte, taille pt, couleur, gras)."""
    return {"paragraphs": [{"textRuns": [{"value": v, "textStyle": {"fontSize": f"{t}pt", "color": c, **({"fontWeight": "bold"} if gras else {})}}
                                         for v, t, c, gras in p]} for p in paragraphes]}


def fond(hexa, bordure=None, rayon=12.0):
    """Conteneur coloré (fond plein, coins arrondis), sans titre."""
    o = {"title": props(show=False), "background": props(show=True, color=couleur(hexa), transparency=0.0),
         "padding": props(top=0.0, bottom=0.0, left=0.0, right=0.0)}
    o["border"] = props(show=True, color=couleur(bordure), radius=rayon) if bordure else props(show=False, radius=rayon)
    return o


def nu(**autres):
    """Conteneur invisible et sans marge intérieure (petites cartes, textes posés sur un fond)."""
    return {"title": props(show=False), "background": props(show=False), "border": props(show=False),
            "padding": props(top=0.0, bottom=0.0, left=0.0, right=0.0), **autres}


def couleurs_entites(champ, propriete="fill"):
    """Une couleur fixe par valeur (catégorie, segment) : la couleur suit l'entité, pas son rang."""
    c = champ["Column"]
    table = COULEURS.get((c["Expression"]["SourceRef"]["Entity"], c["Property"]), {})
    return [{"properties": {propriete: couleur(h)}, "selector": g.selecteur_valeur(champ, v)} for v, h in table.items()]


def series_couleurs(*paires):
    return [{"properties": {"fill": couleur(h)}, "selector": {"metadata": ref(m)}} for m, h in paires]


def conteneur(titre=None, sous_titre=None):
    o = {"title": props(show=bool(titre), **({"text": titre} if titre else {}))}
    if isinstance(sous_titre, dict):  # sous-titre dynamique (mesure)
        o["subTitle"] = props(show=True, text={"expr": sous_titre})
    elif sous_titre:
        o["subTitle"] = props(show=True, text=sous_titre)
    return o


# ---------- Page ----------
class Page:
    def __init__(self, nom, titre, numero, nb_pages):
        self.nom, self.titre, self.numero, self.nb_pages = nom, titre, numero, nb_pages
        self.visuels, self.y = [], 0

    def ajouter(self, cle, x, y, l, h, visuel, filtres=None, principal=True):
        v = {"$schema": g.S_VISUEL, "name": ident("v2", self.nom, cle),
             "position": {"x": round(x, 2), "y": round(y, 2), "z": len(self.visuels) * 1000, "height": round(h, 2),
                          "width": round(l, 2), "tabOrder": len(self.visuels) * 1000},
             "visual": {**visuel, "drillFilterOtherVisuals": True}}
        if filtres:
            v["filterConfig"] = {"filters": filtres}
        self.visuels.append((cle, v))
        if principal:
            self.y = max(self.y, y + h)
        return v

    # --- Barre latérale : fond marine, marque, navigation, segments ---
    def barre_laterale(self, pages):
        self.panneau = self.ajouter("nav-fond", 0, 0, LARGEUR_NAV, 720, {
            "visualType": "textbox",
            "objects": {"general": [{"properties": texte([[("", 10, "#FFFFFF", False)]])}]},
            "visualContainerObjects": fond(MARINE, rayon=0.0)}, principal=False)
        self.ajouter("nav-accent", 24, 26, 34, 4, {
            "visualType": "textbox", "objects": {"general": [{"properties": texte([[("", 6, CIEL, False)]])}]},
            "visualContainerObjects": fond(CIEL, rayon=2.0)}, principal=False)
        self.ajouter("nav-marque", 16, 36, LARGEUR_NAV - 32, 56, {
            "visualType": "textbox",
            "objects": {"general": [{"properties": texte([[("Projet Test", 15, "#FFFFFF", True)],
                                                         [("Tableau de bord commercial", 9, "#B7C9E2", False)]])}]},
            "visualContainerObjects": nu()},
            principal=False)
        for i, (nom, titre) in enumerate(pages):
            actif = nom == self.nom
            # L'onglet est dessiné par une zone de texte (fond blanc si page active) ; un bouton transparent
            # posé dessus assure la navigation. Les « show » d'un bouton se règlent hors des états (sans sélecteur).
            yb = 104 + i * 44
            self.ajouter(f"nav-{nom}-onglet", 16, yb, LARGEUR_NAV - 32, 38, {
                "visualType": "textbox",
                "objects": {"general": [{"properties": texte([[(f"{i + 1:02d}", 9, CIEL if actif else "#8FA9CF", True),
                                                             (f"     {titre}", 11, MARINE if actif else NAV_TEXTE, actif)]])}]},
                "visualContainerObjects": {**(fond("#FFFFFF", rayon=10.0) if actif else nu()),
                                           "padding": props(top=9.0, bottom=0.0, left=14.0, right=0.0)}},
                principal=False)
            self.ajouter(f"nav-{nom}", 16, yb, LARGEUR_NAV - 32, 38, {
                "visualType": "actionButton",
                "objects": {
                    "icon": [{"properties": {"show": lit(False)}}],
                    "text": [{"properties": {"show": lit(False)}}],
                    "fill": [{"properties": {"show": lit(False)}}],
                    "outline": [{"properties": {"show": lit(False)}}],
                },
                "visualContainerObjects": {**nu(), "visualLink": props(show=True, type="PageNavigation", navigationSection=nom),
                                           "visualTooltip": props(show=False)}},
                principal=False)
        y = 104 + len(pages) * 44 + 18
        self.ajouter("filtres-titre", 16, y, LARGEUR_NAV - 32, 26, {
            "visualType": "textbox",
            "objects": {"general": [{"properties": texte([[("FILTRES", 8, "#B7C9E2", True)]])}]},
            "visualContainerObjects": nu()},
            principal=False)
        y += 30
        champs = [
            ("annee", col("Calendrier", "Année"), "Année", {"horizontal": True, "defaut": 2025}),
            ("mois", col("Calendrier", "Mois"), "Mois", {}),
            ("categorie", col("Produits", "categorie"), "Catégorie", {}),
            ("produit", col("Produits", "nom_produit"), "Produit", {"recherche": True}),
            ("segment", col("Clients", "segment"), "Segment", {}),
            ("region", col("Clients", "region"), "Région", {}),
            ("ville", col("Clients", "ville"), "Ville", {"recherche": True}),
            ("client", col("Clients", "nom_client"), "Client", {"recherche": True}),
        ]
        for cle, champ, titre, opt in champs:
            h = 64 if opt.get("horizontal") else 54
            general = {"orientation": lit(1.0 if opt.get("horizontal") else 0.0)}
            if opt.get("recherche"):
                general["selfFilterEnabled"] = lit(True)
            if "defaut" in opt:
                c = champ["Column"]
                general["filter"] = {"filter": {"Version": 2, "From": [{"Name": "c", "Entity": c["Expression"]["SourceRef"]["Entity"], "Type": 0}],
                                                "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": c["Property"]}}],
                                                                                "Values": [[{"Literal": {"Value": f'{opt["defaut"]}L'}}]]}}}]}}
            self.ajouter(f"segment-{cle}", 16, y, LARGEUR_NAV - 32, h, {
                "visualType": "slicer",
                "query": {"queryState": {"Values": {"projections": [proj(champ, titre)]}}},
                "objects": {"general": [{"properties": general}],
                            "data": props(mode="Basic" if opt.get("horizontal") else "Dropdown"),
                            "header": props(show=True, text=titre, fontColor=couleur(ENCRE3), textSize=9.0),
                            "items": props(fontColor=couleur(ENCRE), textSize=10.0),
                            "selection": props(selectAllCheckboxEnabled=not opt.get("horizontal"))},
                "visualContainerObjects": {"title": props(show=False),
                                           "background": props(show=True, color=couleur("#FFFFFF"), transparency=0.0),
                                           "border": props(show=False, radius=10.0),
                                           "padding": props(top=4.0, bottom=4.0, left=8.0, right=8.0)},
                "syncGroup": {"groupName": f"segment-{cle}", "fieldChanges": True, "filterChanges": True}},
                principal=False)
            y += h + 8
        self.y_nav = y

    # --- Bandeau de titre marine ---
    def bandeau(self):
        self.ajouter("bandeau", X0, 20, L_MAIN, 100, {
            "visualType": "textbox",
            "objects": {"general": [{"properties": texte([[(f"{self.numero:02d} / {self.nb_pages:02d}", 9, "#A9C4E8", True)],
                                                         [(self.titre, 22, "#FFFFFF", True)]])}]},
            "visualContainerObjects": {**fond(MARINE, rayon=16.0), "padding": props(top=18.0, bottom=0.0, left=24.0, right=0.0)}})
        self.ajouter("periode", X0 + L_MAIN - 340, 44, 316, 52, {
            "visualType": "card",
            "query": {"queryState": {"Values": {"projections": [proj(mes("Libellé période"), "Période")]}}},
            "objects": {"labels": props(fontSize=13.0, color=couleur("#FFFFFF")),
                        "categoryLabels": props(show=True, color=couleur("#A9C4E8"), fontSize=8.0)},
            "visualContainerObjects": {"title": props(show=False), "background": props(show=True, color=couleur(CIEL), transparency=72.0),
                                       "border": props(show=False, radius=12.0),
                                       "padding": props(top=4.0, bottom=4.0, left=0.0, right=0.0)}})
        return 20 + 100 + GOUT

    # --- Tuiles KPI : cadre blanc, trait bleu ciel, valeur, ligne d'évolution / de contexte ---
    def kpis(self, tuiles, y):
        n = len(tuiles)
        l = (L_MAIN - (n - 1) * 12) / n
        for i, (lib, mesure, txt, couleur_txt) in enumerate(tuiles):
            x = X0 + i * (l + 12)
            self.ajouter(f"kpi-{i}-cadre", x, y, l, 108, {
                "visualType": "textbox", "objects": {"general": [{"properties": texte([[("", 8, ENCRE, False)]])}]},
                "visualContainerObjects": fond(SURFACE, bordure="#D3E3F6", rayon=12.0)})
            self.ajouter(f"kpi-{i}", x, y + 10, l, 62, {
                "visualType": "card",
                "query": {"queryState": {"Values": {"projections": [proj(mes(mesure))]}}},
                "objects": {"labels": props(fontSize=19.0, color=couleur(MARINE), labelDisplayUnits=0.0, fontFamily=POLICE_GRAS),
                            "categoryLabels": props(show=False)},
                "visualContainerObjects": nu(title=props(show=True, text=lib, fontColor=couleur(ENCRE3), fontSize=9.0, bold=True,
                                                         alignment="center"))})
            self.ajouter(f"kpi-{i}-texte", x + 6, y + 74, l - 12, 28, {
                "visualType": "card",
                "query": {"queryState": {"Values": {"projections": [proj(mes(txt))]}}},
                "objects": {"labels": props(fontSize=8.5, color=couleur_mesure(couleur_txt) if couleur_txt else couleur(ENCRE3)),
                            "categoryLabels": props(show=False)},
                "visualContainerObjects": nu()})
        return y + 108 + GOUT

    def visuel(self, cle, c, y, span, h, type_, titre, sous_titre, roles, objets=None, tri_=None, filtres=None):
        v = {"visualType": type_, "query": {"queryState": {r: {"projections": p} for r, p in roles.items()}},
             "visualContainerObjects": conteneur(titre, sous_titre)}
        if tri_:
            v["query"]["sortDefinition"] = tri_
        if objets:
            v["objects"] = objets
        self.ajouter(cle, x_col(c), y, l_col(span), h, v, filtres)

    def ecrire(self, dossier):
        hauteur = int(max(self.y + MARGE, self.y_nav + MARGE, 720))
        self.panneau["position"]["height"] = hauteur
        d = dossier / self.nom
        (d / "visuals").mkdir(parents=True)
        ecrire_json(d / "page.json", {"$schema": g.S_PAGE, "name": self.nom, "displayName": self.titre,
                                       "displayOption": "FitToWidth", "height": hauteur, "width": L_PAGE})
        for _, v in self.visuels:
            ecrire_json(d / "visuals" / v["name"] / "visual.json", v)
        return hauteur


# ---------- Raccourcis de formatage ----------
LEGENDE_HAUT = {"legend": props(show=True, position="Top")}
SANS_LEGENDE = {"legend": props(show=False)}
ETIQUETTES = {"labels": props(show=True, color=couleur(ENCRE2))}
UNIE = {"dataPoint": [{"properties": {"fill": couleur(PRIMAIRE)}}]}

MOIS_ANNEE = col("Calendrier", "Mois-Année")
CA, CA_N1 = mes("Chiffre d'affaires"), mes("CA N-1")
EVOL = mes("Évolution CA vs N-1 (%)")
CAT, SEG, REGION = col("Produits", "categorie"), col("Clients", "segment"), col("Clients", "region")
CLIENT, PRODUIT = col("Clients", "nom_client"), col("Produits", "nom_produit")
SOUS_TITRE_PONT = mes("Sous-titre pont")


def cascade(p, cle, c, y, span, h, titre, champ, mesure, tri_):
    """Graphique en cascade : une barre par étape, hausses en vert, baisses en rouge, total en marine."""
    p.visuel(cle, c, y, span, h, "waterfallChart", titre, SOUS_TITRE_PONT,
             {"Category": [proj(champ)], "Y": [proj(mesure, "Écart")]},
             {"sentimentColors": props(increaseFill=couleur(BON), decreaseFill=couleur(MAUVAIS), totalFill=couleur(PRIMAIRE)),
              "labels": props(show=True, color=couleur(ENCRE2), labelDisplayUnits=1000.0),
              "legend": props(show=True, position="Top")}, tri_)


def empile100(p, cle, c, y, span, h, titre, sous_titre, champ):
    p.visuel(cle, c, y, span, h, "hundredPercentStackedBarChart", titre, sous_titre,
             {"Category": [proj(champ)], "Series": [proj(SEG, "Segment")], "Y": [proj(CA)]},
             {**LEGENDE_HAUT, "labels": props(show=True, color=couleur("#FFFFFF")), "dataPoint": couleurs_entites(SEG)}, tri(CA))


# ---------- Pages ----------
def page_overview(p):
    y = p.kpis([
        ("Chiffre d'affaires", "Chiffre d'affaires", "Libellé évol. CA", "Couleur évol. CA"),
        ("CA cumul annuel", "CA cumul annuel", "Libellé évol. CA cumul", "Couleur évol. CA cumul"),
        ("Nombre de ventes", "Nombre de ventes", "Libellé évol. ventes", "Couleur évol. ventes"),
        ("Panier moyen", "Panier moyen", "Libellé évol. panier", "Couleur évol. panier"),
        ("Clients actifs", "Clients actifs", "Libellé évol. clients", "Couleur évol. clients"),
        ("Nouveaux clients", "Nouveaux clients", "Texte nouveaux clients", None),
        ("Taux de remise", "Taux de remise", "Texte remises", None),
    ], p.bandeau())
    p.visuel("ca-mois", 0, y, 8, 330, "lineChart", "Chiffre d'affaires par mois",
             "Période sélectionnée comparée à la même période un an plus tôt",
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Y": [proj(CA, "Période"), proj(CA_N1, "Même période N-1")]},
             {**LEGENDE_HAUT, "dataPoint": series_couleurs((CA, PRIMAIRE), (CA_N1, N1))}, tri(MOIS_ANNEE, "Ascending"))
    p.visuel("ca-segment", 8, y, 4, 330, "donutChart", "CA par segment client", None,
             {"Category": [proj(SEG, "Segment")], "Y": [proj(CA)]},
             {"dataPoint": couleurs_entites(SEG), "legend": props(show=True, position="Bottom"),
              "labels": props(show=True, labelStyle="Percent of total")})
    y += 330 + GOUT
    cascade(p, "pont-categories", 0, y, 6, 340, "Écart vs N-1 : contribution des catégories", CAT,
            mes("Évolution CA vs N-1 (€)"), tri(mes("Évolution CA vs N-1 (€)")))
    p.visuel("repartition", 6, y, 6, 340, "treemap", "Répartition du CA", "Par catégorie puis par produit · surface proportionnelle au CA",
             {"Group": [proj(CAT, "Catégorie")], "Details": [proj(PRODUIT, "Produit")], "Values": [proj(CA)]},
             {"dataPoint": couleurs_entites(CAT), "labels": props(show=True), "categoryLabels": props(show=True),
              "legend": props(show=True, position="Top")})
    y += 340 + GOUT
    for i, (cle, champ, titre) in enumerate([("ca-categorie", CAT, "CA par catégorie"), ("ca-region", REGION, "CA par région")]):
        p.visuel(cle, 6 * i, y, 6, 300, "clusteredBarChart", titre, "Montant du chiffre d'affaires",
                 {"Category": [proj(champ)], "Y": [proj(CA)]}, {**ETIQUETTES, **SANS_LEGENDE, **UNIE}, tri(CA))
    y += 300 + GOUT
    for i, (cle, champs, titre) in enumerate([("top-produits", [PRODUIT, CAT], "Top 5 produits"),
                                              ("top-clients", [CLIENT, SEG], "Top 5 clients")]):
        p.visuel(cle, 6 * i, y, 6, 240, "tableEx", titre, "Classés par chiffre d'affaires",
                 {"Values": [proj(champs[0]), proj(champs[1]), proj(CA, "CA"), proj(EVOL, "vs N-1")]},
                 {"values": [g.couleur_texte_colonne(EVOL, "Couleur évol. CA")]}, tri(CA), [filtre_top(champs[0], 5, CA)])


def page_clients(p):
    y = p.kpis([
        ("Clients actifs", "Clients actifs", "Libellé évol. clients", "Couleur évol. clients"),
        ("Taux de clients actifs", "Taux de clients actifs", "Texte portefeuille", None),
        ("Nouveaux clients", "Nouveaux clients", "Texte nouveaux", None),
        ("Taux de rétention", "Taux de rétention", "Texte rétention", None),
        ("Clients perdus", "Clients perdus", "Texte perdus", None),
        ("CA moyen par client", "CA moyen par client", "Libellé évol. CA moyen client", "Couleur évol. CA moyen client"),
        ("Fréquence d'achat", "Fréquence d'achat", "Texte fréquence", None),
        ("Part CA top 10", "Part du CA des 10 premiers clients", "Texte concentration", None),
    ], p.bandeau())
    etape = col("Pont clients", "Étape")
    cascade(p, "pont-clients", 0, y, 6, 340, "Variation du CA par type de client", etape, mes("Montant pont clients"),
            tri(etape, "Ascending"))
    part = mes("Part cumulée du CA")
    p.visuel("concentration", 6, y, 6, 340, "lineChart", "Concentration du CA", mes("Texte concentration 20 %"),
             {"Category": [proj(CLIENT, "Clients, du plus gros au plus petit")], "Y": [proj(part)]},
             {**SANS_LEGENDE, "dataPoint": series_couleurs((part, PRIMAIRE)),
              "categoryAxis": props(show=False),   # 120 noms de clients : l'axe n'apporte rien, la courbe suffit
              "valueAxis": props(start=0.0, end=1.0)}, tri(part, "Ascending"))
    y += 340 + GOUT
    empile100(p, "region-segment", 0, y, 12, 330, "Répartition du CA par région et segment",
              "Part de chaque segment dans le CA de la région", REGION)
    y += 330 + GOUT
    actifs, nouveaux = mes("Clients actifs"), mes("Nouveaux clients")
    p.visuel("clients-mois", 0, y, 6, 300, "lineChart", "Clients actifs et nouveaux clients par mois", "Nombre de clients distincts",
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Y": [proj(actifs), proj(nouveaux)]},
             {**LEGENDE_HAUT, "dataPoint": series_couleurs((actifs, PRIMAIRE), (nouveaux, CIEL))}, tri(MOIS_ANNEE, "Ascending"))
    p.visuel("segment-n1", 6, y, 6, 300, "clusteredBarChart", "CA par segment client", "Période comparée à N-1",
             {"Category": [proj(SEG, "Segment")], "Y": [proj(CA, "Période"), proj(CA_N1, "Même période N-1")]},
             {**LEGENDE_HAUT, **ETIQUETTES, "dataPoint": series_couleurs((CA, PRIMAIRE), (CA_N1, N1))}, tri(CA))
    y += 300 + GOUT
    for i, (cle, m, titre) in enumerate([("actifs-region", actifs, "Clients actifs par région"),
                                         ("moyen-region", mes("CA moyen par client"), "CA moyen par client et par région")]):
        p.visuel(cle, 6 * i, y, 6, 300, "clusteredBarChart", titre, None,
                 {"Category": [proj(REGION, "Région")], "Y": [proj(m)]}, {**ETIQUETTES, **SANS_LEGENDE, **UNIE}, tri(m))
    y += 300 + GOUT
    p.visuel("profil", 0, y, 6, 340, "scatterChart", "Profil des clients", "Panier moyen selon le nombre d'achats · taille = CA",
             {"Category": [proj(CLIENT, "Client")], "Series": [proj(SEG, "Segment")],
              "X": [proj(mes("Nombre de ventes"), "Nombre d'achats")], "Y": [proj(mes("Panier moyen"))], "Size": [proj(CA)]},
             {**LEGENDE_HAUT, "dataPoint": couleurs_entites(SEG)})
    p.visuel("top10", 6, y, 6, 340, "clusteredBarChart", "Top 10 clients", "Classés par chiffre d'affaires",
             {"Category": [proj(CLIENT, "Client")], "Y": [proj(CA)]}, {**ETIQUETTES, **SANS_LEGENDE, **UNIE}, tri(CA),
             [filtre_top(CLIENT, 10, CA)])
    y += 340 + GOUT
    p.visuel("detail-clients", 0, y, 12, 440, "tableEx", "Détail des clients", "Clients actifs sur la période · cliquer un en-tête pour trier",
             {"Values": [proj(mes("Rang client"), "#"), proj(CLIENT, "Client"), proj(SEG, "Segment"),
                         proj(col("Clients", "ville"), "Ville"), proj(REGION, "Région"), proj(CA, "CA"), proj(CA_N1, "CA N-1"),
                         proj(EVOL, "Évolution"), proj(mes("Nombre de ventes"), "Ventes"), proj(mes("Panier moyen")),
                         proj(mes("Date du dernier achat"), "Dernier achat"), proj(mes("Récence (jours)"))]},
             {"values": [g.couleur_texte_colonne(EVOL, "Couleur évol. CA")]}, tri(CA))


def page_ventes(p):
    y = p.kpis([
        ("Chiffre d'affaires", "Chiffre d'affaires", "Libellé évol. CA", "Couleur évol. CA"),
        ("Quantité vendue", "Quantité vendue", "Libellé évol. quantité", "Couleur évol. quantité"),
        ("Nombre de ventes", "Nombre de ventes", "Libellé évol. ventes", "Couleur évol. ventes"),
        ("Prix moyen de vente", "Prix moyen de vente", "Libellé évol. prix moyen", "Couleur évol. prix moyen"),
        ("Montant des remises", "Montant des remises", "Texte taux de remise", None),
        ("Produits vendus", "Nombre de produits vendus", "Texte catalogue", None),
    ], p.bandeau())
    mm3 = mes("CA moyenne mobile 3 mois")
    p.visuel("ca-mois", 0, y, 8, 330, "lineClusteredColumnComboChart", "Chiffre d'affaires par mois", "Avec la moyenne mobile sur 3 mois",
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Y": [proj(CA)], "Y2": [proj(mm3, "Moyenne mobile 3 mois")]},
             {**LEGENDE_HAUT, "dataPoint": series_couleurs((CA, PRIMAIRE), (mm3, CIEL))}, tri(MOIS_ANNEE, "Ascending"))
    cum, cum1, mois = mes("CA cumul annuel"), mes("CA cumul annuel N-1"), col("Calendrier", "Mois")
    p.visuel("cumul", 8, y, 4, 330, "lineChart", "CA cumulé sur l'année", "Comparé à l'année précédente",
             {"Category": [proj(mois)], "Y": [proj(cum, "Année"), proj(cum1, "Année N-1")]},
             {**LEGENDE_HAUT, "dataPoint": series_couleurs((cum, PRIMAIRE), (cum1, N1))}, tri(mois, "Ascending"))
    y += 330 + GOUT
    etape = col("Pont prix", "Étape")
    cascade(p, "pont-prix", 0, y, 6, 340, "Variation du CA : volume, prix, mix", etape, mes("Montant pont prix"), tri(etape, "Ascending"))
    empile100(p, "categorie-segment", 6, y, 6, 340, "Répartition du CA par catégorie et segment",
              "Qui achète quoi : part de chaque segment client", CAT)
    y += 340 + GOUT
    ecart = mes("Évolution CA vs N-1 (€)")
    p.visuel("evol-categorie", 0, y, 6, 300, "clusteredBarChart", "Évolution du CA vs N-1 par catégorie", "Écart en euros",
             {"Category": [proj(CAT, "Catégorie")], "Y": [proj(ecart, "Écart vs N-1")]},
             {**ETIQUETTES, **SANS_LEGENDE, "dataPoint": g.couleur_par_point("Couleur écart vs N-1")}, tri(ecart))
    p.visuel("ca-categorie-mois", 6, y, 6, 300, "lineChart", "CA mensuel par catégorie", None,
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Series": [proj(CAT, "Catégorie")], "Y": [proj(CA)]},
             {**LEGENDE_HAUT, "dataPoint": couleurs_entites(CAT)}, tri(MOIS_ANNEE, "Ascending"))
    y += 300 + GOUT
    mom = mes("Évolution vs mois précédent (%)")
    p.visuel("evol-mois", 0, y, 12, 240, "clusteredColumnChart", "Évolution vs mois précédent", None,
             {"Category": [proj(MOIS_ANNEE, "Mois")], "Y": [proj(mom, "vs mois précédent")]},
             {**ETIQUETTES, **SANS_LEGENDE, "dataPoint": g.couleur_par_point("Couleur évol. mois")}, tri(MOIS_ANNEE, "Ascending"))
    y += 240 + GOUT
    gradient = {"expr": {"FillRule": {"Input": CA, "FillRule": {"linearGradient2": {
        "min": {"color": {"Literal": {"Value": f"'{SURFACE}'"}}},
        "max": {"color": {"Literal": {"Value": f"'{SERIES[0]}'"}}},
        "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}}
    p.visuel("matrice", 0, y, 12, 560, "pivotTable", "CA par produit et par mois", "Catégories puis produits",
             {"Rows": [proj(CAT, "Catégorie"), proj(PRODUIT, "Produit")], "Columns": [proj(MOIS_ANNEE, "Mois")], "Values": [proj(CA, "CA")]},
             {"values": [{"properties": {"backColor": {"solid": {"color": gradient}}},
                          "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": ref(CA)}}]}, tri(CA))
    y += 560 + GOUT
    p.visuel("detail-produits", 0, y, 12, 440, "tableEx", "Détail des produits", "Cliquer un en-tête pour trier",
             {"Values": [proj(mes("Rang produit"), "#"), proj(PRODUIT, "Produit"), proj(CAT, "Catégorie"),
                         proj(mes("Quantité vendue"), "Quantité"), proj(CA, "CA"), proj(CA_N1, "CA N-1"), proj(ecart, "Écart"),
                         proj(EVOL, "Évolution"), proj(mes("Part du CA")), proj(mes("Prix moyen de vente"), "Prix moyen"),
                         proj(mes("Taux de remise"))]},
             {"values": [g.couleur_texte_colonne(EVOL, "Couleur évol. CA")]}, tri(CA))


# ---------- Thème ----------
def theme():
    police = lambda taille, c, gras=False: {"fontFace": "Segoe UI Semibold" if gras else "Segoe UI", "fontSize": taille, "color": c}
    solide = lambda h: {"solid": {"color": h}}
    return {
        "name": "ProjetTestV2",
        "dataColors": SERIES,
        "good": BON, "neutral": GRILLE, "bad": MAUVAIS,
        "maximum": SERIES[0], "center": "#8FB4EE", "minimum": "#DBE8FB",
        "background": SURFACE, "foreground": ENCRE, "tableAccent": MARINE,
        "textClasses": {"title": police(12, MARINE, True), "header": police(10, ENCRE2, True), "label": police(10, ENCRE2),
                        "callout": police(20, MARINE, True)},
        "visualStyles": {
            "*": {"*": {
                "background": [{"show": True, "color": solide(SURFACE), "transparency": 0}],
                "border": [{"show": True, "color": solide(BORD), "radius": 12}],
                "dropShadow": [{"show": False}],
                "title": [{"show": True, "fontColor": solide(MARINE), "fontSize": 12, "bold": True}],
                "subTitle": [{"fontColor": solide(ENCRE3), "fontSize": 9}],
                "valueAxis": [{"gridlineColor": solide(GRILLE), "gridlineStyle": "solid", "labelColor": solide(ENCRE3), "showAxisTitle": False}],
                "categoryAxis": [{"labelColor": solide(ENCRE3), "showAxisTitle": False}],
                "legend": [{"labelColor": solide(ENCRE2), "fontSize": 9}],
                "lineStyles": [{"strokeWidth": 2}],
                "visualTooltip": [{"titleFontColor": solide(MARINE), "valueFontColor": solide(ENCRE), "background": solide(SURFACE)}],
            }},
            "page": {"*": {"background": [{"color": solide(PAGE_FOND), "transparency": 0}],
                           "outspace": [{"color": solide(PAGE_FOND)}]}},
            "tableEx": {"*": {"columnHeaders": [{"fontColor": solide(ENCRE3), "backColor": solide(SURFACE_2), "bold": True}],
                              "grid": [{"gridHorizontalColor": solide(GRILLE), "gridVertical": False}]}},
            "pivotTable": {"*": {"columnHeaders": [{"fontColor": solide(ENCRE3), "backColor": solide(SURFACE_2), "bold": True}],
                                 "rowHeaders": [{"fontColor": solide(ENCRE)}]}},
        },
    }


def main():
    titres = [("overview", "Overview"), ("clients", "Clients"), ("ventes", "Ventes")]
    construire = {"overview": page_overview, "clients": page_clients, "ventes": page_ventes}
    pages = []
    for i, (nom, titre) in enumerate(titres):
        p = Page(nom, titre, i + 1, len(titres))
        p.barre_laterale(titres)
        construire[nom](p)
        pages.append(p)

    shutil.rmtree(DEF / "pages", ignore_errors=True)
    hauteurs = [p.ecrire(DEF / "pages") for p in pages]
    ecrire_json(DEF / "pages" / "pages.json", {"$schema": g.S_PAGES, "pageOrder": [p.nom for p in pages], "activePageName": pages[0].nom})
    ecrire_json(DEF / "version.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"})
    ecrire_json(DEF / "report.json", {
        "$schema": g.S_RAPPORT,
        "themeCollection": {
            "baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.59", "type": "SharedResources"},
            "customTheme": {"name": "ProjetTestV2.json", "reportVersionAtImport": "5.59", "type": "RegisteredResources"}},
        "layoutOptimization": "None",
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "ProjetTestV2.json", "path": "ProjetTestV2.json", "type": "CustomTheme"}]}],
    })
    ressources = RAPPORT / "StaticResources"
    ecrire_json(ressources / "RegisteredResources" / "ProjetTestV2.json", theme())
    base = ressources / "SharedResources" / "BaseThemes" / "CY24SU10.json"
    base.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(g.RAPPORT / "StaticResources" / "SharedResources" / "BaseThemes" / "CY24SU10.json", base)
    ecrire_json(RAPPORT / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": "../ProjetTest.SemanticModel"}}})
    ecrire_json(RAPPORT / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": "ProjetTestV2"},
        "config": {"version": "2.0", "logicalId": "6f1d2c7e-4b8a-4e0f-9a51-2c3d8e7b9f10"}})
    ecrire_json(RACINE / "ProjetTestV2.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": "ProjetTestV2.Report"}}], "settings": {"enableAutoRecovery": True}})
    for p, h in zip(pages, hauteurs):
        print(f"{p.titre} : {len(p.visuels)} visuels, hauteur {h} px")


if __name__ == "__main__":
    main()
