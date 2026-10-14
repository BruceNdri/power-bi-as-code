"""Crée dist/ProjetTest.zip : les rapports v1 et v2 (.pbip et dossiers) et leur modèle commun,
à copier en un seul bloc sur le poste Windows."""
import pathlib
import zipfile

RACINE = pathlib.Path(__file__).resolve().parent.parent
SORTIE = RACINE / "dist" / "ProjetTest.zip"

fichiers = [RACINE / "ProjetTest.pbip", RACINE / "ProjetTestV2.pbip"] + [
    p for d in ("ProjetTest.Report", "ProjetTestV2.Report", "ProjetTest.SemanticModel")
    for p in sorted((RACINE / d).rglob("*"))
    if p.is_file() and ".pbi" not in p.parts  # .pbi : réglages et cache locaux de Desktop
]
SORTIE.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(SORTIE, "w", zipfile.ZIP_DEFLATED) as z:
    for p in fichiers:
        z.write(p, "ProjetTest/" + p.relative_to(RACINE).as_posix())
print(f"{SORTIE.relative_to(RACINE)} : {len(fichiers)} fichiers")
