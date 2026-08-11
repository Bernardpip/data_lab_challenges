from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


FILES = {
    "formations":
        "file-formations-techniques-etablissements-06-01-2025-17-53-15.csv",

    "formations_detail":
        "formations-techniques-etablissements.csv",

    "depenses":
        "depenses-publiques-par-etudiant-enseignement-superieur-du-pib-par-habitant-.csv",

    "chomage":
        "chomage-des-diplomes-de-lenseignement-superieur-de-la-population-active-totale-diplomee-de-lenseignement-superieur-.csv",

    "inscriptions":
        "inscriptions-scolaires-enseignement-superieur-brut-.csv",

    "etablissements":
        "repartition-des-etablissements-denseignement-superieur-ayant-fonctionne-par-type-statut-et-localisation-geographique.csv",

    "budget":
        "observationdata-acikief.csv",

    # 9ᵉ ressource — indicateurs clés du supérieur (DICES-TG). C'est le seul
    # fichier du corpus qui porte des effectifs ABSOLUS, la féminisation, la
    # part des filières scientifiques et le ratio étudiant/enseignant : les
    # quatre indicateurs de l'objectif n°2 du cahier des charges.
    "indicateurs_sup":
        "observationdata-fspjmfg.csv",
}



def load_csv(filename):

    path = DATA_DIR / filename

    print(f"Chargement : {path}")

    return pd.read_csv(
        path,
        encoding="utf-8",
        low_memory=False
    )



def load_all_data():

    data={}

    for key,file in FILES.items():
        data[key]=load_csv(file)


    return data