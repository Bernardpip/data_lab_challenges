"""Génère le rapport PowerPoint (10 pages maximum) attendu comme livrable.

    python scripts/generer_presentation.py            # les deux langues
    python scripts/generer_presentation.py fr         # une seule

Ce fichier ne porte que **les 10 pages** — ce que ce défi-ci raconte. Le
bandeau de titre, le pied, la tuile de chiffre-clé, le bloc d'analyse, le
style des graphes natifs, l'objet `Langue` et l'assemblage bilingue viennent
de `socle.rapport`.

Trois choix qui ne se renégocient pas :

  · les graphiques sont NATIFS PowerPoint (`add_chart`), donc éditables et
    redimensionnables par le lecteur — pas des images figées ;
  · tous les chiffres sont recalculés par `collecter()` depuis les MÊMES
    fonctions que le tableau de bord : la présentation ne peut pas diverger
    de l'écran ;
  · `collecter()` est appelé UNE seule fois pour les deux langues. Deux
    chargements laisseraient les versions diverger sur un arrondi.

Les 10 pages de la trame :

    1. Couverture                    6. Économétrie
    2. Données, nettoyage, démarche  7. Moyens publics
    3. Le constat structurant        8. Le croisement attendu (et ses limites)
    4. Sa dynamique dans le temps    9. Leviers d'action
    5. L'effet mis en évidence      10. Conclusion et limites
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

# pyrefly: ignore [missing-import]
from pptx.chart.data import CategoryChartData                   # noqa: E402
# pyrefly: ignore [missing-import]
from pptx.enum.chart import XL_CHART_TYPE                       # noqa: E402
# pyrefly: ignore [missing-import]
from pptx.util import Inches                                    # noqa: E402

from socle import i18n                                          # noqa: E402

i18n.configurer(RACINE / "i18n" / "locales")

from socle.i18n import LANGUES                                  # noqa: E402
from socle.rapport import charte, generer_toutes                # noqa: E402



def page_1_couverture(prs, c, lg):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    boite = slide.shapes.add_textbox(Inches(0.9), Inches(2.2), Inches(11.5),
                                     Inches(3.0))
    cadre = boite.text_frame
    cadre.word_wrap = True

    charte.texte(cadre, lg.t("p1_titre"), taille=40, gras=True, premier=True,
                 espace_apres=10)
    charte.texte(cadre, lg.t("p1_sous_titre"), taille=16,
                 couleur=charte.ENCRE_SECONDAIRE, espace_apres=22)
    charte.texte(cadre, lg.t("p1_accroche", {
        "cantons": lg.nb(c["cantons"]),
        "part": lg.nb(c["part_pop_exposee"], 0),
    }), taille=13, couleur=charte.ENCRE, espace_apres=26)
    charte.texte(cadre, lg.t("p1_auteur"), taille=12, couleur=charte.MUTED)


def page_2_demarche(prs, c, lg):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 2, lg.t("p2_titre"), lg.t("p2_sous_titre"))

    tuiles = [
        (lg.nb(c["jeux"]), "p2_t1", "p2_t1_d"),
        (lg.nb(c["cantons"]), "p2_t2", "p2_t2_d"),
        (lg.nb(c["ouvrages"]), "p2_t3", "p2_t3_d"),
        (f'{c["publies"]} / {c["decrits"]}', "p2_t4", "p2_t4_d"),
    ]

    for index, (valeur, libelle, detail) in enumerate(tuiles):
        charte.bloc_constat(
            slide, Inches(0.6 + index * 3.1), Inches(1.85), Inches(2.9),
            Inches(1.3), valeur=valeur, libelle=lg.t(libelle),
            detail=lg.t(detail),
        )

    for index, cle in enumerate(("p2_etape_1", "p2_etape_2", "p2_etape_3")):
        charte.bloc_analyse(
            slide, Inches(0.6 + index * 4.15), Inches(3.5), Inches(3.9),
            Inches(2.6), nom=lg.t(f"{cle}_nom"), question=lg.t(f"{cle}_q"),
            resultat=lg.t(f"{cle}_r"), lecture=lg.t(f"{cle}_l"),
        )

    charte.pied(slide, 2, lg)


def page_3_concentration(prs, c, lg):
    """Le constat structurant : 4 % des cantons, 35 % du pays."""

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 3, lg.t("p3_titre"), lg.t("p3_sous_titre"))

    _barres(slide, prs, lg, Inches(0.6), Inches(1.8), Inches(7.3), Inches(4.6),
            categories=[lg.t(f"classe_{cle}") for cle in c["classes_cles"]],
            valeurs=c["classes_population"], titre=lg.t("p3_graphe"))

    charte.bloc_constat(
        slide, Inches(8.3), Inches(2.0), Inches(4.3), Inches(1.4),
        valeur=lg.nb(c["cantons_exposes"]), libelle=lg.t("p3_t1"),
        detail=lg.t("p3_t1_d", {"part": lg.nb(c["part_cantons_exposes"], 0)}),
        couleur=charte.DANGER,
    )
    charte.bloc_constat(
        slide, Inches(8.3), Inches(3.5), Inches(4.3), Inches(1.4),
        valeur=lg.compact(c["population_exposee"]), libelle=lg.t("p3_t2"),
        detail=lg.t("p3_t2_d", {"part": lg.nb(c["part_pop_exposee"], 0)}),
        couleur=charte.DANGER,
    )
    charte.bloc_analyse(
        slide, Inches(8.3), Inches(5.0), Inches(4.3), Inches(1.5),
        nom=lg.t("p3_lecture_nom"), question=lg.t("p3_lecture_q"),
        resultat=lg.t("p3_lecture_r"), lecture=lg.t("p3_lecture_l"),
    )

    charte.pied(slide, 3, lg)


def page_4_seuils(prs, c, lg):
    """Ce que le corpus ne dit pas : les seuils officiels, et la méthode."""

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 4, lg.t("p4_titre"), lg.t("p4_sous_titre"))

    for index, cle in enumerate(("p4_a", "p4_b")):
        charte.bloc_analyse(
            slide, Inches(0.6), Inches(1.9 + index * 2.3), Inches(6.0),
            Inches(2.1), nom=lg.t(f"{cle}_nom"), question=lg.t(f"{cle}_q"),
            resultat=lg.t(f"{cle}_r"), lecture=lg.t(f"{cle}_l"),
        )

    charte.bloc_constat(
        slide, Inches(7.1), Inches(2.0), Inches(5.5), Inches(1.5),
        valeur=f'{c["fri_reproductible"]} / {c["cantons"]}',
        libelle=lg.t("p4_t1"), detail=lg.t("p4_t1_d"),
    )
    charte.bloc_constat(
        slide, Inches(7.1), Inches(3.7), Inches(5.5), Inches(1.5),
        valeur=lg.nb(c["absents"]), libelle=lg.t("p4_t2"),
        detail=lg.t("p4_t2_d", {"decrits": c["decrits"]}),
        couleur=charte.DANGER,
    )

    charte.pied(slide, 4, lg)


def page_5_couverture(prs, c, lg):
    """La pression démographique face à l'inventaire."""

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 5, lg.t("p5_titre"), lg.t("p5_sous_titre"))

    _barres(slide, prs, lg, Inches(0.6), Inches(1.8), Inches(7.3), Inches(4.6),
            categories=c["regions"], valeurs=c["regions_hab_ouvrage"],
            titre=lg.t("p5_graphe"))

    charte.bloc_constat(
        slide, Inches(8.3), Inches(2.0), Inches(4.3), Inches(1.4),
        valeur=lg.compact(c["plateaux_hab_ouvrage"]), libelle=lg.t("p5_t1"),
        detail=lg.t("p5_t1_d"), couleur=charte.DANGER,
    )
    charte.bloc_analyse(
        slide, Inches(8.3), Inches(3.6), Inches(4.3), Inches(2.8),
        nom=lg.t("p5_lecture_nom"), question=lg.t("p5_lecture_q"),
        resultat=lg.t("p5_lecture_r", {
            "national": lg.compact(c["national_hab_ouvrage"])}),
        lecture=lg.t("p5_lecture_l"),
    )

    charte.pied(slide, 5, lg)


def page_6_croisement(prs, c, lg):
    """Le croisement attendu : le risque est-il couvert ?"""

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 6, lg.t("p6_titre"), lg.t("p6_sous_titre"))

    _barres(slide, prs, lg, Inches(0.6), Inches(1.8), Inches(7.3), Inches(4.6),
            categories=[lg.t(f"classe_{cle}") for cle in c["classes_cles"]],
            valeurs=c["classes_part_equipee"], titre=lg.t("p6_graphe"))

    charte.bloc_analyse(
        slide, Inches(8.3), Inches(2.0), Inches(4.3), Inches(2.2),
        nom=lg.t("p6_a_nom"), question=lg.t("p6_a_q"),
        resultat=lg.t("p6_a_r", {
            "sans": lg.nb(100 * c["r2_besoin"], 0),
            "avec": lg.nb(100 * c["r2_region"], 0)}),
        lecture=lg.t("p6_a_l"),
    )
    charte.bloc_constat(
        slide, Inches(8.3), Inches(4.5), Inches(4.3), Inches(1.6),
        valeur=lg.nb(c["prioritaires"]), libelle=lg.t("p6_t1"),
        detail=lg.t("p6_t1_d", {
            "population": lg.compact(c["population_prioritaire"])}),
        couleur=charte.DANGER,
    )

    charte.pied(slide, 6, lg)


def page_7_cout(prs, c, lg):
    """Le résultat qui commande les autres : le coût est plat."""

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 7, lg.t("p7_titre"), lg.t("p7_sous_titre"))

    _barres(slide, prs, lg, Inches(0.6), Inches(1.8), Inches(7.3), Inches(4.6),
            categories=[lg.t(f"p7_q{index}") for index in range(1, 6)],
            valeurs=c["cout_par_quintile"], titre=lg.t("p7_graphe"))

    charte.bloc_constat(
        slide, Inches(8.3), Inches(2.0), Inches(4.3), Inches(1.4),
        valeur=lg.compact(c["cout_median"]), libelle=lg.t("p7_t1"),
        detail=lg.t("p7_t1_d"),
    )
    charte.bloc_analyse(
        slide, Inches(8.3), Inches(3.6), Inches(4.3), Inches(2.8),
        nom=lg.t("p7_lecture_nom"), question=lg.t("p7_lecture_q"),
        resultat=lg.t("p7_lecture_r", {"rapport": lg.nb(c["ecart_cout"], 0)}),
        lecture=lg.t("p7_lecture_l"),
    )

    charte.pied(slide, 7, lg)


def page_8_allocation(prs, c, lg):
    """L'argent suit-il les habitants ? Non — et cela coûte des bénéficiaires."""

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 8, lg.t("p8_titre"), lg.t("p8_sous_titre"))

    charte.bloc_constat(
        slide, Inches(0.6), Inches(1.9), Inches(3.9), Inches(1.5),
        valeur=lg.nb(c["elasticite"], 2), libelle=lg.t("p8_t1"),
        detail=lg.t("p8_t1_d", {"n": c["cantons_dotes"]}), couleur=charte.DANGER,
    )
    charte.bloc_constat(
        slide, Inches(4.7), Inches(1.9), Inches(3.9), Inches(1.5),
        valeur=lg.nb(c["gini"], 2), libelle=lg.t("p8_t2"),
        detail=lg.t("p8_t2_d", {"rapport": lg.nb(c["interdecile"], 1)}),
    )
    charte.bloc_constat(
        slide, Inches(8.8), Inches(1.9), Inches(3.8), Inches(1.5),
        valeur=lg.compact(c["budget_paye"]), libelle=lg.t("p8_t3"),
        detail=lg.t("p8_t3_d", {"ecart": lg.nb(c["ecart_appel_offres"], 0)}),
    )

    for index, cle in enumerate(("p8_a", "p8_b")):
        charte.bloc_analyse(
            slide, Inches(0.6 + index * 6.3), Inches(3.7), Inches(6.0),
            Inches(2.5), nom=lg.t(f"{cle}_nom"), question=lg.t(f"{cle}_q"),
            resultat=lg.t(f"{cle}_r"), lecture=lg.t(f"{cle}_l"),
        )

    charte.pied(slide, 8, lg)


def page_9_leviers(prs, c, lg):
    """Trois leviers, par coût croissant."""

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 9, lg.t("p9_titre"), lg.t("p9_sous_titre"))

    for index in range(1, 4):
        charte.bloc_analyse(
            slide, Inches(0.6), Inches(1.85 + (index - 1) * 1.65),
            Inches(12.1), Inches(1.5),
            nom=lg.t(f"p9_l{index}_nom"), question=lg.t(f"p9_l{index}_q"),
            resultat=lg.t(f"p9_l{index}_r", {
                "cantons": lg.nb(c["prioritaires"]),
                "absents": lg.nb(c["absents"]),
                "cout": lg.nb(c["cout_beneficiaire"], 0),
            }),
            lecture=lg.t(f"p9_l{index}_l"),
        )

    charte.pied(slide, 9, lg)


def page_10_conclusion(prs, c, lg):
    """Ce que le corpus établit, et ce qu'il refuse d'établir."""

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    charte.titre_page(slide, 10, lg.t("p10_titre"), lg.t("p10_sous_titre"))

    for index, cle in enumerate(("p10_a", "p10_b")):
        charte.bloc_analyse(
            slide, Inches(0.6 + index * 6.3), Inches(1.9), Inches(6.0),
            Inches(2.4), nom=lg.t(f"{cle}_nom"), question=lg.t(f"{cle}_q"),
            resultat=lg.t(f"{cle}_r"), lecture=lg.t(f"{cle}_l"),
        )

    boite = slide.shapes.add_textbox(Inches(0.6), Inches(4.6), Inches(12.1),
                                     Inches(2.0))
    cadre = boite.text_frame
    cadre.word_wrap = True
    charte.texte(cadre, lg.t("p10_limites_titre"), taille=12, gras=True,
                 couleur=charte.PRIMAIRE, premier=True, espace_apres=6)

    for index in range(1, 4):
        charte.texte(cadre, lg.t(f"p10_limite_{index}"), taille=10,
                     couleur=charte.ENCRE_SECONDAIRE, espace_apres=4)

    charte.pied(slide, 10, lg)


def _barres(slide, prs, lg, gauche, haut, largeur, hauteur, categories,
            valeurs, titre):
    """Un graphe à barres NATIF — éditable par le lecteur, pas une image.

    Regroupé ici plutôt que répété dans cinq pages : le seul écart entre
    elles est le couple (catégories, valeurs), et une image figée priverait
    le destinataire du droit de retoucher la figure dans son propre document.
    """

    donnees = CategoryChartData()
    donnees.categories = categories
    donnees.add_series(titre, tuple(valeurs))

    cadre = slide.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED, gauche, haut, largeur, hauteur, donnees
    )
    charte.style_graphe(cadre.chart, titre)
    cadre.chart.has_legend = False

    return cadre.chart


PAGES = [
    page_1_couverture,
    page_2_demarche,
    page_3_concentration,
    page_4_seuils,
    page_5_couverture,
    page_6_croisement,
    page_7_cout,
    page_8_allocation,
    page_9_leviers,
    page_10_conclusion,
]


def collecter():
    """Tous les chiffres du rapport, calculés depuis les jeux nettoyés.

    Appelée UNE fois et partagée entre les deux langues. Chaque valeur vient
    d'`utils.analytics`, d'`utils.econometrie` ou d'`utils.perimetre`, jamais
    d'un calcul écrit ici : un chiffre recalculé à deux endroits finit
    toujours par diverger, et c'est le tableau de bord qui fait foi.
    """

    from utils.data import datasets
    from utils import analytics, econometrie, perimetre

    data = datasets()
    cantons, tde, coso = data["cantons"], data["tde"], data["coso"]

    faits = analytics.synthese(cantons, tde, coso, data["ventes"])
    classes = analytics.population_par_classe(cantons)
    matrice = analytics.matrice_risque_equipement(cantons, tde, coso)
    hautes = classes[classes["classe_officielle"].isin(analytics.CLASSES_HAUTES)]
    prioritaires = analytics.cantons_prioritaires(cantons, tde, coso)

    cout = econometrie.fonction_de_cout(coso)
    elasticite = econometrie.elasticite_investissement(cantons, coso)
    equipe = econometrie.qui_est_equipe(cantons, tde, coso)
    couverture = econometrie.couverture_par_region(cantons, tde, coso)
    contre = econometrie.contrefactuel_demographique(cantons, coso)
    reconstitution = analytics.reconstitution_fri(cantons)

    ecart = perimetre.ecart_publication()
    budget = analytics.chaine_budgetaire(coso).set_index("etape")["montant"]
    profil = cout["profil"]["cout_par_beneficiaire"]

    geometrique = reconstitution[
        reconstitution["forme"] == "moyenne_geometrique"]

    return {
        "jeux": len(data),
        "cantons": faits["cantons"],
        "ouvrages": faits["tde_total"] + faits["coso_total"],
        "decrits": ecart["decrits"],
        "publies": ecart["communs"],
        "absents": ecart["absents"],

        "classes_cles": list(classes["classe_officielle"]),
        "classes_population": classes["population"].tolist(),
        "classes_part_equipee": matrice["part_equipee"].round(1).tolist(),
        "cantons_exposes": int(hautes["cantons"].sum()),
        "part_cantons_exposes": 100 * hautes["cantons"].sum() / faits["cantons"],
        "population_exposee": float(hautes["population"].sum()),
        "part_pop_exposee": float(hautes["part_population"].sum()),

        "fri_reproductible": int(geometrique["cantons"].iloc[0])
        if not geometrique.empty else 0,

        "regions": couverture["regions"]["region"].tolist(),
        "regions_hab_ouvrage": couverture["regions"][
            "habitants_par_ouvrage"].fillna(0).round(0).tolist(),
        "national_hab_ouvrage": couverture["national"],
        "plateaux_hab_ouvrage": float(
            couverture["regions"]["habitants_par_ouvrage"].max()),

        "r2_besoin": equipe["sans_region"]["r2"],
        "r2_region": equipe["avec_region"]["r2"],
        "prioritaires": len(prioritaires),
        "population_prioritaire": float(prioritaires["population"].sum()),

        "cout_median": cout["cout_median"],
        "cout_par_quintile": profil.round(0).tolist(),
        "ecart_cout": float(profil.iloc[0] / profil.iloc[-1]),
        "cout_beneficiaire": float(analytics.cout_par_beneficiaire(coso)
                                   ["cout_beneficiaire"].median()),

        "elasticite": float(
            elasticite["simple"]["termes"].iloc[1]["coefficient"]),
        "cantons_dotes": elasticite["cantons"],
        "gini": contre["gini"],
        "interdecile": contre["rapport_interdecile"],
        "budget_paye": float(budget["paye"]),
        "ecart_appel_offres": 100 * (
            1 - budget["contracte"] / budget["estime"]),
    }


if __name__ == "__main__":
    demandees = sys.argv[1:] or list(LANGUES)
    partages = collecter()

    for code, chemin, pages in generer_toutes(
        PAGES, partages, langues=demandees, dossier=RACINE / "rapport"
    ):
        print(f"[{code}] {pages} pages → {chemin}")
