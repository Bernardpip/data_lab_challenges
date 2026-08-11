"""Analyses économétriques — estimations, tests et interprétations.

Chaque modèle est présenté avec son diagnostic complet (n, R², p-value,
intervalle de confiance) ET une interprétation qui dit explicitement ce que le
résultat autorise à conclure — y compris quand la réponse est « rien ».

Deux modèles de cette page ne sont PAS significatifs. Ils sont conservés et
affichés comme tels : un résultat non concluant est une information, et le
masquer donnerait une fausse impression de solidité à l'ensemble.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle import charts
from socle.ui import card, note, stat_tiles, fr_number
from socle.design.tokens import STATUS
from utils.data import datasets, bruts
from socle.stats import econometrie as eco
from utils import analytics, perimetre
from socle.i18n.traduction import t


def _badge(modele, seuil_n=10):
    """Pastille de fiabilité d'une estimation, fondée sur p-value ET effectif."""

    tr = t("econometrie")

    if modele is None:
        return "", tr("badge_non_estimable")

    if not modele.get("significatif"):
        return STATUS["critical"], tr("badge_non_significatif")

    if modele["n"] < seuil_n:
        return STATUS["warning"], tr("badge_significatif_faible_n", {"n": modele["n"]})

    return STATUS["good"], tr("badge_significatif", {"n": modele["n"]})


def _diagnostic(modele, unite=""):
    """Bloc de diagnostic standard sous chaque estimation."""

    tr = t("econometrie")

    if modele is None:
        st.info(tr("info_estimation_impossible"))
        return

    couleur, libelle = _badge(modele)

    p = modele["p_value"]
    p_texte = "< 0,001" if p < 0.001 else fr_number(p, 4)

    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:18px;align-items:center;'
        'padding:10px 12px;background:var(--kg-color-surface-secondary);'
        'border-radius:6px;font-size:var(--kg-fs-xs);margin:4px 0 8px 0;">'
        f'<span style="display:inline-flex;align-items:center;gap:6px;font-weight:600;">'
        f'<span style="width:8px;height:8px;border-radius:9999px;background:{couleur};"></span>'
        f'{libelle}</span>'
        f'<span><b>{tr("diag_coefficient")}</b> {fr_number(modele["pente"], 3)} {unite}</span>'
        f'<span><b>{tr("diag_ic")}</b> [{fr_number(modele["ic_bas"], 3)} ; '
        f'{fr_number(modele["ic_haut"], 3)}]</span>'
        f'<span><b>R²</b> {fr_number(modele["r2"], 3)}</span>'
        f'<span><b>p</b> {p_texte}</span>'
        f'<span><b>n</b> {modele["n"]}</span>'
        "</div>",
        unsafe_allow_html=True
    )


def render_modeles():
    tr = t("econometrie")

    data = datasets()
    inscriptions = data["inscriptions"]
    depenses = data["depenses"]

    tendance_ins = eco.tendance_temporelle(inscriptions)
    tendance_dep = eco.tendance_temporelle(depenses)
    elast = eco.elasticite(inscriptions, depenses)
    rupture = eco.rupture_de_tendance(inscriptions, 2000)

    stat_tiles([
        {"label": tr("tuile_tendance_inscriptions"),
         "value": "+" + fr_number(tendance_ins["par_decennie"], 1),
         "unit": tr("unite_pts_decennie"), "icon": "trending-up",
         "delta": tr("tuile_diag", {"r2": fr_number(tendance_ins["r2"], 2),
                                    "n": tendance_ins["n"]}),
         "good": True},
        {"label": tr("tuile_tendance_depense"),
         "value": fr_number(tendance_dep["par_decennie"], 0),
         "unit": tr("unite_pts_decennie"), "icon": "wallet",
         "delta": tr("tuile_diag", {"r2": fr_number(tendance_dep["r2"], 2),
                                    "n": tendance_dep["n"]}),
         "good": False},
        {"label": tr("tuile_elasticite"),
         "value": fr_number(elast["elasticite"], 2), "icon": "bar-chart-3",
         "delta": tr("tuile_elasticite_detail"), "good": False},
        {"label": tr("tuile_acceleration"),
         "value": "×" + fr_number(rupture["rapport"], 1), "icon": "flag",
         "delta": tr("tuile_acceleration_detail"), "good": True},
    ])

    # ─── Modèle 1 ───────────────────────────────────────────────────────────
    with card(tr("m1_titre"), tr("m1_sous_titre"), "trending-up"):
        _diagnostic(tendance_ins, unite=tr("unite_pt_an"))
        charts.scatter_fit(
            inscriptions["annee"], inscriptions["valeur"],
            labels=inscriptions["annee"].astype(int),
            modele=tendance_ins,
            x_titre=tr("m1_axe_x"), y_titre=tr("m1_axe_y"),
        )
        note(tr("m1_note", {
            "par_an": fr_number(tendance_ins["par_an"], 2),
            "par_decennie": fr_number(tendance_ins["par_decennie"], 1),
            "r2": fr_number(tendance_ins["r2"] * 100, 0),
            "n": tendance_ins["n"],
        }))

    # ─── Modèle 2 ───────────────────────────────────────────────────────────
    with card(tr("m2_titre"), tr("m2_sous_titre"), "wallet"):
        _diagnostic(tendance_dep, unite=tr("unite_pt_an"))
        charts.scatter_fit(
            depenses["annee"], depenses["valeur"],
            labels=depenses["annee"].astype(int),
            modele=tendance_dep,
            x_titre=tr("m1_axe_x"), y_titre=tr("m2_axe_y"),
        )
        note(tr("m2_note", {
            "par_an": fr_number(abs(tendance_dep["par_an"]), 1),
            "par_decennie": fr_number(abs(tendance_dep["par_decennie"]), 0),
            "n": tendance_dep["n"],
        }))

    # ─── Modèle 3 ───────────────────────────────────────────────────────────
    with card(tr("m3_titre"), tr("m3_sous_titre"), "bar-chart-3"):
        _diagnostic(elast)
        note(tr("m3_note", {
            "elasticite": fr_number(elast["elasticite"], 2),
            "amplitude": fr_number(abs(elast["elasticite"]), 2),
            "ic_bas": fr_number(elast["ic_bas"], 2),
            "ic_haut": fr_number(elast["ic_haut"], 2),
            "n": elast["n"],
        }))

    # ─── Modèle 4 ───────────────────────────────────────────────────────────
    with card(tr("m4_titre"), tr("m4_sous_titre"), "flag"):
        gauche, droite = st.columns(2, gap="small")

        with gauche:
            st.markdown(tr("m4_avant"))
            _diagnostic(rupture["avant"], unite=tr("unite_pt_an"))

        with droite:
            st.markdown(tr("m4_apres"))
            _diagnostic(rupture["apres"], unite=tr("unite_pt_an"))

        # Le recouvrement des intervalles est CALCULÉ, pas affirmé : c'est lui
        # qui décide si l'accélération est objectivée ou seulement apparente.
        disjoints = (rupture["avant"]["ic_haut"] < rupture["apres"]["ic_bas"]
                     or rupture["apres"]["ic_haut"] < rupture["avant"]["ic_bas"])

        note(tr("m4_note", {
            "avant": fr_number(rupture["avant"]["pente"], 3),
            "apres": fr_number(rupture["apres"]["pente"], 3),
            "rapport": fr_number(rupture["rapport"], 1),
            "verdict": tr("m4_verdict_disjoints" if disjoints
                          else "m4_verdict_recouvrent"),
        }))


def render_limites():
    tr = t("econometrie")

    data = datasets()
    formations = data["formations"]

    correl_dep = eco.correlation(data["inscriptions"], data["depenses"])
    correl_cho = eco.correlation(data["inscriptions"], data["chomage"])
    execution = eco.execution_vs_montant(data["budget"])
    conc = eco.concentration(analytics.par_region(formations)["etablissements"].tolist())

    # ─── Concentration ──────────────────────────────────────────────────────
    with card(tr("conc_titre"), tr("conc_sous_titre"), "map-pin"):
        stat_tiles([
            {"label": tr("tuile_hhi"), "value": fr_number(conc["hhi"], 3),
             "icon": "bar-chart-3",
             "delta": tr("tuile_hhi_detail",
                         {"equilibre": fr_number(conc["hhi_equilibre"], 2)}),
             "good": False},
            {"label": tr("tuile_hhi_norm"),
             "value": fr_number(conc["hhi_normalise"], 3), "icon": "trending-up",
             "delta": tr("tuile_hhi_norm_detail"), "good": False},
            {"label": tr("tuile_gini"), "value": fr_number(conc["gini"], 3),
             "icon": "flag", "delta": tr("tuile_gini_detail"), "good": False},
            {"label": tr("tuile_part_max"),
             "value": fr_number(conc["part_max"] * 100, 1), "unit": "%",
             "icon": "map-pin",
             "delta": tr("tuile_part_max_detail", {"unites": conc["unites"]}),
             "good": False},
        ])
        note(tr("conc_note", {
            "hhi": fr_number(conc["hhi"], 3),
            "equilibre": fr_number(conc["hhi_equilibre"], 2),
            "gini": fr_number(conc["gini"], 2),
        }))

    # ─── Corrélations ───────────────────────────────────────────────────────
    with card(tr("correl_titre"), tr("correl_sous_titre"), "search"):
        valeurs = {
            "dep_pr": fr_number(correl_dep["pearson_r"], 2),
            "dep_pp": fr_number(correl_dep["pearson_p"], 4),
            "dep_sr": fr_number(correl_dep["spearman_r"], 2),
            "dep_sp": fr_number(correl_dep["spearman_p"], 3),
            "dep_n": correl_dep["n"],
            "cho_pr": fr_number(correl_cho["pearson_r"], 2),
            "cho_pp": fr_number(correl_cho["pearson_p"], 3),
            "cho_sr": fr_number(correl_cho["spearman_r"], 2),
            "cho_sp": fr_number(correl_cho["spearman_p"], 3),
            "cho_n": correl_cho["n"],
        }
        st.markdown(tr("correl_tableau", valeurs))
        note(tr("correl_note", dict(valeurs,
                                    cho_pp=fr_number(correl_cho["pearson_p"], 2))))

    # ─── Modèle non significatif ────────────────────────────────────────────
    with card(tr("m5_titre"), tr("m5_sous_titre"), "wallet"):
        _diagnostic(execution, unite=tr("unite_pt_par_hausse"))

        if execution:
            charts.scatter_fit(
                execution["observations"]["variation_vote"],
                execution["observations"]["taux"],
                labels=execution["observations"]["annee"].astype(int),
                modele=execution,
                x_titre=tr("m5_axe_x"), y_titre=tr("m5_axe_y"),
                height=280,
            )

        note(tr("m5_note", {
            "pente": fr_number(execution["pente"], 2),
            "r2": fr_number(execution["r2"], 2),
            "n": execution["n"],
            "p": fr_number(execution["p_value"], 2),
            "ic_bas": fr_number(execution["ic_bas"], 2),
            "ic_haut": fr_number(execution["ic_haut"], 2),
        }))

    # ─── Ce que les données ne permettent pas ───────────────────────────────
    inventaire = perimetre.audit(bruts())
    ecart = inventaire["ecart"]
    hors_portee = [
        l for l in inventaire["lignes"] if l["verdict"] == perimetre.IMPOSSIBLE
    ]

    with card(tr("hors_portee_titre", {"nombre": len(hors_portee)}),
              tr("hors_portee_sous_titre"), "flag"):
        st.markdown(tr("hors_portee_corps", {
            "total": inventaire["total"],
            "nombre": len(hors_portee),
            "decrits": ecart["decrits"],
            "publies": ecart["publies"],
            "absents": ecart["absents"],
            "champs_eleves": "`, `".join(ecart["familles"]["Effectifs d'élèves"][:2]),
        }))

        blocs = []

        for entree in hors_portee:
            blocs.append(
                '<div style="padding:10px 0;border-bottom:1px solid '
                'var(--kg-color-border-light);">'
                f'<div style="font-weight:600;">{entree["indicateur"]}</div>'
                '<div style="color:var(--kg-color-text-secondary);margin-top:3px;">'
                f'{entree["motif"]}</div>'
                '<div style="color:var(--kg-color-text-muted);'
                'font-size:var(--kg-fs-xs);margin-top:3px;">'
                f'{entree["objectif"]}  ·  {entree["source"]}</div>'
                "</div>"
            )

        st.markdown("".join(blocs), unsafe_allow_html=True)

        note(tr("hors_portee_note_1"))
        note(tr("hors_portee_note_2", {"absents": ecart["absents"]}))
