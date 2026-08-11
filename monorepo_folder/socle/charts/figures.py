"""Graphes — construits selon la méthode data-viz, pas au goût du jour.

Règles appliquées partout, sans exception :
  · la FORME découle du job de la donnée (magnitude / identité / polarité /
    évolution) ; un chiffre seul n'est pas un graphe (→ `ui.stat_tiles`) ;
  · la COULEUR découle du job, jamais du rang : nominal = une seule teinte
    (slot 1), séries distinctes = slots catégoriels dans l'ordre figé,
    magnitude = rampe séquentielle une teinte, polarité = divergente ;
  · marques fines : barres ≤ 24px à bout arrondi 4px, lignes 2px, marqueurs
    ≥ 8px cerclés de 2px de surface, grille hairline pleine (jamais pointillée) ;
  · le TEXTE porte les tokens d'encre, jamais la couleur de série ;
  · labels directs parcimonieux + survol partout + jumeau tableau (`table_twin`)
    pour qu'aucune valeur ne soit accessible par la seule couleur ;
  · jamais deux axes Y : deux mesures d'échelles différentes → `line_indexed`.
"""

import numpy as np
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go
# pyrefly: ignore [missing-import]
import streamlit as st

from socle.design.tokens import (
    SERIES, SEQUENTIAL, DIVERGING, INK, TYPOGRAPHY,
)
from socle.i18n.traduction import t

_FONT = TYPOGRAPHY["fontFamily"]

# Épaisseur de barre : fraction de bande telle que la marque reste ≤ 24px.
_BAR_WIDTH = 0.55
_ROW_H = 34

# Séparateurs plotly : virgule décimale + espace fine insécable en milliers.
# Vaut pour les ticks d'axe ET les infobulles.
_SEPARATORS = ", "


def _fr(value, decimals=0, signed=False):
    """Nombre au format français, pour les libellés directs."""

    text = f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")

    if signed and value > 0:
        return "+" + text

    return text.replace("-", "−")


def _base_layout(height, show_legend=False, margin_l=0):
    """Chrome commun : fond transparent (la carte fournit la surface), grille
    hairline, encre muted, survol systématique."""

    return dict(
        height=height,
        margin=dict(l=margin_l, r=16, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT, size=11, color=INK["muted"]),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            font=dict(size=11, color=INK["secondary"]),
            bgcolor="rgba(0,0,0,0)",
            # Sans ça, plotly inverse la légende des barres empilées : elle ne
            # correspondrait plus à l'ordre des segments.
            traceorder="normal",
        ),
        hoverlabel=dict(
            bgcolor=INK["surface"],
            bordercolor=INK["axis"],
            font=dict(family=_FONT, size=12, color=INK["primary"]),
        ),
        barcornerradius=4,
        separators=_SEPARATORS,
    )


def _axis(show_grid=True, show_line=False, tickformat=None,
          tick_size=11, tick_color=None):
    """Axe hairline plein (jamais pointillé), encre muted par défaut ;
    `tick_color`/`tick_size` pour l'axe qui porte les libellés de catégorie."""

    return dict(
        showgrid=show_grid,
        gridcolor=INK["grid"],
        gridwidth=1,
        zeroline=False,
        showline=show_line,
        linecolor=INK["axis"],
        linewidth=1,
        ticks="",
        tickfont=dict(size=tick_size, color=tick_color or INK["muted"]),
        tickformat=tickformat,
        automargin=True,
    )


def _category_axis():
    """Axe des catégories : encre primaire, un cran plus grand que les ticks."""

    return _axis(show_grid=False, tick_size=12, tick_color=INK["primary"])


def _show(fig, key=None):
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "scrollZoom": False},
        key=key,
    )


def table_twin(df, label=None):
    """Jumeau tableau — obligatoire : aucune valeur n'est lisible seulement
    par la couleur ou le survol.

    Le libellé par défaut est résolu À L'APPEL, pas à la définition : écrit en
    valeur par défaut de la signature, il aurait été figé au français une fois
    pour toutes, au chargement du module, avant même qu'une langue soit choisie.
    """

    with st.expander(label or t("commun")("voir_donnees")):
        st.dataframe(df, use_container_width=True, hide_index=True)


# ─── Magnitude, catégories nominales ────────────────────────────────────────

def bar_h(df, cat, val, unit="", highlight=None, max_rows=None, height=None):
    """Barres horizontales, catégories NOMINALES → une seule teinte pour toutes.

    Colorer chaque barre selon sa valeur re-encoderait la longueur : la teinte
    reste constante et la longueur seule porte la magnitude. `highlight` bascule
    en forme « emphase » : une barre en couleur, le reste en gris de retrait.
    `height` force la hauteur (colonne étroite) — sinon calculée depuis le
    nombre de barres.
    """

    data = df.sort_values(val, ascending=True)

    if max_rows:
        data = data.tail(max_rows)

    labels = data[cat].astype(str).tolist()
    values = data[val].tolist()

    if highlight is None:
        colors = SERIES[0]
    else:
        colors = [
            SERIES[0] if str(label) == str(highlight) else INK["deemphasis"]
            for label in labels
        ]

    text = [_fr(v) + (f" {unit}" if unit else "") for v in values]

    fig = go.Figure(
        go.Bar(
            x=values, y=labels,
            orientation="h",
            marker=dict(color=colors),
            width=_BAR_WIDTH,
            text=text,
            textposition="outside",
            textfont=dict(size=11, color=INK["secondary"], family=_FONT),
            cliponaxis=False,
            hovertemplate="%{y} · %{x:,.0f} " + unit + "<extra></extra>",
        )
    )

    fig.update_layout(**_base_layout(height or max(140, len(labels) * _ROW_H + 30)))
    # Toutes les barres sont étiquetées → l'axe de valeur ferait doublon.
    fig.update_xaxes(**_axis(show_grid=False), visible=False,
                     range=[0, max(values) * 1.18 if values else 1])
    fig.update_yaxes(**_category_axis())

    _show(fig)


def column_series(labels, values, unit="", height=260, highlight=None, note_last=None):
    """Colonnes verticales — catégories ORDONNÉES (décennies, paliers).

    L'ordre porte du sens : on garde donc l'axe horizontal du temps, et une
    seule teinte (la magnitude est dans la hauteur, pas dans la couleur).
    `highlight` passe en forme « emphase » sur un libellé.
    """

    labels = [str(label) for label in labels]

    if highlight is None:
        colors = SERIES[0]
    else:
        colors = [
            SERIES[0] if label == str(highlight) else INK["deemphasis"]
            for label in labels
        ]

    fig = go.Figure(
        go.Bar(
            x=labels, y=list(values),
            marker=dict(color=colors),
            width=0.6,
            text=[_fr(v) for v in values],
            textposition="outside",
            textfont=dict(size=11, color=INK["secondary"], family=_FONT),
            cliponaxis=False,
            hovertemplate="%{x} · %{y:,.0f} " + unit + "<extra></extra>",
        )
    )

    fig.update_layout(**_base_layout(height))
    fig.update_xaxes(**_axis(show_grid=False, show_line=True, tick_color=INK["primary"]))

    # Des libellés d'années sont relus par Plotly comme une échelle continue,
    # d'où des graduations à la demi-année. On force le pas à 1 — sans passer
    # l'axe en catégories, qui masquerait les années SANS mesure en collant
    # les colonnes les unes aux autres.
    _annees_entieres(fig, [{"x": labels}])

    # Toutes les colonnes sont étiquetées → l'axe de valeur ferait doublon.
    fig.update_yaxes(**_axis(show_grid=False), visible=False,
                     range=[0, max(values) * 1.18 if len(values) else 1])

    if note_last:
        fig.add_annotation(
            x=labels[-1], y=values[-1],
            text=note_last, showarrow=False, yshift=28,
            font=dict(size=10, color=INK["muted"], family=_FONT),
        )

    _show(fig)


def scatter_fit(x, y, labels=None, modele=None, x_titre="", y_titre="",
                height=300, log=False):
    """Nuage de points + droite de régression estimée.

    Forme « toutes paires » (deux points quelconques peuvent se toucher) : une
    seule teinte, l'identité passe par l'infobulle. La droite est tracée sur la
    PLAGE OBSERVÉE uniquement — jamais extrapolée au-delà.
    """

    xs = np.asarray(x, dtype=float)
    ys = np.asarray(y, dtype=float)

    fig = go.Figure()

    # Droite d'abord, pour qu'elle passe SOUS les points.
    if modele:
        bornes = np.array([xs.min(), xs.max()])
        ajuste = modele["ordonnee"] + modele["pente"] * bornes

        fig.add_trace(
            go.Scatter(
                x=bornes, y=ajuste,
                mode="lines",
                line=dict(color=INK["deemphasis"], width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter(
            x=xs, y=ys,
            mode="markers",
            marker=dict(size=9, color=SERIES[0],
                        line=dict(color=INK["surface"], width=2)),
            text=[str(label) for label in labels] if labels is not None else None,
            hovertemplate=(
                ("%{text}<br>" if labels is not None else "")
                + "%{x:,.2f} · %{y:,.2f}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    fig.update_layout(**_base_layout(height))
    fig.update_xaxes(**_axis(show_grid=False, show_line=True),
                     title=dict(text=x_titre, font=dict(size=11, color=INK["muted"])))
    fig.update_yaxes(**_axis(show_grid=True),
                     title=dict(text=y_titre, font=dict(size=11, color=INK["muted"])))

    _show(fig)


# ─── Part-à-tout ────────────────────────────────────────────────────────────

def bar_stacked_h(df, cat, series_cols, unit=""):
    """Barres empilées horizontales — part-à-tout par catégorie.

    Les segments sont séparés par 2px de SURFACE (l'espace fait la séparation,
    pas un contour). Légende obligatoire dès deux séries.
    """

    data = df.copy()
    data["_total"] = data[series_cols].sum(axis=1)
    data = data.sort_values("_total", ascending=True)

    labels = data[cat].astype(str).tolist()
    fig = go.Figure()

    for index, col in enumerate(series_cols):
        fig.add_trace(
            go.Bar(
                x=data[col].tolist(), y=labels,
                name=col,
                orientation="h",
                width=_BAR_WIDTH,
                marker=dict(
                    color=SERIES[index],
                    line=dict(color=INK["surface"], width=2),
                ),
                hovertemplate="%{y} · " + col + " : %{x:,.0f} " + unit + "<extra></extra>",
            )
        )

    fig.update_layout(
        **_base_layout(max(150, len(labels) * _ROW_H + 46), show_legend=True),
        barmode="stack",
    )
    fig.update_xaxes(**_axis(show_grid=True))
    fig.update_yaxes(**_category_axis())

    _show(fig)


# ─── Évolution ──────────────────────────────────────────────────────────────

def line_series(series, x_title=None, unit="", height=260, end_labels=True):
    """Une ou plusieurs séries temporelles.

    `series` : liste de dicts {name, x, y}. Ligne 2px, marqueurs 8px cerclés de
    surface, valeur en bout de série uniquement (jamais sur chaque point).
    Une seule série → pas de boîte de légende (le titre de la carte la nomme).

    Une série peut fixer son emplacement de couleur avec `slot`. C'est
    indispensable dès qu'un filtre peut retirer une série : sans cela, masquer
    la première repeindrait toutes les suivantes, et la couleur suivrait le
    rang au lieu de l'entité.
    """

    fig = go.Figure()
    multiple = len(series) > 1

    for index, serie in enumerate(series):
        color = SERIES[serie.get("slot", index) % len(SERIES)]
        xs, ys = list(serie["x"]), list(serie["y"])

        fig.add_trace(
            go.Scatter(
                x=xs, y=ys,
                name=serie["name"],
                mode="lines+markers",
                line=dict(color=color, width=2, shape="linear"),
                marker=dict(
                    size=8, color=color,
                    line=dict(color=INK["surface"], width=2),
                ),
                hovertemplate="%{x} · %{y:,.2f} " + unit + "<extra>" + serie["name"] + "</extra>",
            )
        )

        # Label direct au bout de la ligne — l'extrémité, pas chaque point.
        if end_labels and xs:
            fig.add_annotation(
                x=xs[-1], y=ys[-1],
                text="  " + _fr(ys[-1], 1) + (f" {unit}" if unit else ""),
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color=INK["secondary"], family=_FONT),
            )

    fig.update_layout(
        **_base_layout(height, show_legend=multiple),
        hovermode="x unified",
    )
    fig.update_xaxes(**_axis(show_grid=False, show_line=True), title=None)
    fig.update_yaxes(**_axis(show_grid=True))

    _annees_entieres(fig, series)

    _show(fig)


def _annees_entieres(fig, series):
    """Empêche les graduations à la demi-année sur un axe de temps court.

    Sur une série de trois points (2016, 2017, 2019), Plotly choisit un pas de
    0,5 et affiche « 2 016,5 » — une année qui n'existe pas, et mise en forme
    comme un nombre. On force le pas à l'année dès que l'amplitude est courte ;
    au-delà, Plotly choisit bien tout seul et un pas de 1 saturerait l'axe.
    """

    brut = [v for serie in series for v in serie["x"]]

    if not brut:
        return

    # Les libellés peuvent être des chaînes (« 2016 ») : Plotly les relit comme
    # des nombres, la correction doit donc s'appliquer aussi à ce cas.
    try:
        valeurs = [float(v) for v in brut]
    except (TypeError, ValueError):
        return

    etendue = max(valeurs) - min(valeurs)

    if etendue <= 12:
        fig.update_xaxes(dtick=1, tickformat="d")


def line_indexed(series, base_year, unit="base 100", height=280):
    """Deux mesures d'échelles différentes sur UN SEUL axe, indexées à 100 à
    `base_year` — la réponse honnête au graphe à double axe, qui inventerait
    une corrélation en alignant arbitrairement deux échelles."""

    fig = go.Figure()

    # Repère 100 : hairline pleine, pas de pointillé.
    fig.add_hline(y=100, line=dict(color=INK["axis"], width=1))

    for index, serie in enumerate(series):
        color = SERIES[index]
        xs, ys = list(serie["x"]), list(serie["y"])

        fig.add_trace(
            go.Scatter(
                x=xs, y=ys,
                name=serie["name"],
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=8, color=color, line=dict(color=INK["surface"], width=2)),
                hovertemplate="%{x} · indice %{y:,.0f}<extra>" + serie["name"] + "</extra>",
            )
        )

        if xs:
            fig.add_annotation(
                x=xs[-1], y=ys[-1],
                text="  " + _fr(ys[-1]),
                showarrow=False, xanchor="left",
                font=dict(size=11, color=INK["secondary"], family=_FONT),
            )

    fig.update_layout(**_base_layout(height, show_legend=True), hovermode="x unified")
    fig.update_xaxes(**_axis(show_grid=False, show_line=True))
    fig.update_yaxes(**_axis(show_grid=True), title=dict(
        text=f"indice {unit} ({base_year} = 100)",
        font=dict(size=11, color=INK["muted"]),
    ))

    _annees_entieres(fig, series)

    _show(fig)


# ─── Polarité ───────────────────────────────────────────────────────────────

def diverging_bar(labels, values, unit="pts", height=None):
    """Écart de part et d'autre d'une ligne de base — job de POLARITÉ.

    Deux teintes qui se lisent comme opposées (bleu / rouge) ; le milieu est un
    gris neutre, jamais une teinte.
    """

    colors = [DIVERGING["pos"] if v >= 0 else DIVERGING["neg"] for v in values]
    text = [_fr(v, 1, signed=True) + f" {unit}" for v in values]

    fig = go.Figure(
        go.Bar(
            x=values, y=[str(label) for label in labels],
            orientation="h",
            marker=dict(color=colors),
            width=_BAR_WIDTH,
            text=text,
            textposition="outside",
            textfont=dict(size=11, color=INK["secondary"], family=_FONT),
            cliponaxis=False,
            hovertemplate="%{y} · %{x:+,.1f} " + unit + "<extra></extra>",
        )
    )

    span = max(abs(min(values)), abs(max(values))) * 1.45 if values else 1

    # Le côté sans valeur reste VISIBLE mais étroit : « aucune année au-dessus
    # du voté » est une information, une demi-toile vide n'en est pas une.
    gauche = -span if min(values) < 0 else -span * 0.3
    droite = span if max(values) > 0 else span * 0.3

    fig.update_layout(**_base_layout(height or max(140, len(labels) * _ROW_H + 30)))
    fig.add_vline(x=0, line=dict(color=INK["axis"], width=1))
    fig.update_xaxes(**_axis(show_grid=False), visible=False, range=[gauche, droite])
    fig.update_yaxes(**_category_axis())

    _show(fig)


# ─── Magnitude sur grille ───────────────────────────────────────────────────

def heatmap(matrix, unit="", height=None):
    """Grille de magnitude — rampe SÉQUENTIELLE une seule teinte, clair→foncé.

    Les valeurs sont écrites dans les cases : la couleur ne porte jamais seule
    l'information (et l'encre s'inverse sur les cases foncées).
    """

    values = matrix.values
    peak = values.max() if values.size else 1

    text = [[("" if v == 0 else _fr(v)) for v in row] for row in values]
    text_colors = [
        [INK["surface"] if v > peak * 0.55 else INK["secondary"] for v in row]
        for row in values
    ]

    fig = go.Figure(
        go.Heatmap(
            z=values,
            x=[str(c) for c in matrix.columns],
            y=[str(i) for i in matrix.index],
            colorscale=[[i / (len(SEQUENTIAL) - 1), c] for i, c in enumerate(SEQUENTIAL)],
            xgap=2, ygap=2,  # 2px de surface entre les cases
            hovertemplate="%{y} · %{x} : %{z:,.0f} " + unit + "<extra></extra>",
            colorbar=dict(
                thickness=8, len=0.85, outlinewidth=0,
                tickfont=dict(size=10, color=INK["muted"]),
            ),
        )
    )

    for row_index, row in enumerate(text):
        for col_index, cell in enumerate(row):
            if cell:
                fig.add_annotation(
                    x=col_index, y=row_index, text=cell, showarrow=False,
                    font=dict(size=11, family=_FONT,
                              color=text_colors[row_index][col_index]),
                )

    fig.update_layout(**_base_layout(height or max(180, len(matrix.index) * 42 + 50)))
    fig.update_xaxes(**_axis(show_grid=False, tick_color=INK["secondary"]), side="top")
    # Sans ça, plotly dessine la première ligne EN BAS : la grille se lirait
    # à l'envers de l'ordre de tri.
    fig.update_yaxes(**_category_axis(), autorange="reversed")

    _show(fig)


def sucette_h(df, cat, val, unit="", highlight=None, max_rows=None, height=None,
              decimals=0):
    """Barres-sucettes horizontales — MAGNITUDE sur beaucoup de catégories.

    Même job que `bar_h`, mais lisible bien au-delà : à vingt lignes, une barre
    pleine sature la carte d'encre et les libellés s'écrasent contre la masse.
    La sucette ne garde que ce qui porte l'information — la LONGUEUR de la tige
    et la position du point — et rend la valeur au bout, en clair.

    Une seule teinte, comme pour toute magnitude sur catégories nominales : la
    couleur ne re-encode jamais ce que la longueur dit déjà.
    """

    data = df[[cat, val]].dropna().sort_values(val, ascending=True)

    if max_rows:
        data = data.tail(max_rows)

    labels = data[cat].astype(str).tolist()
    values = data[val].tolist()
    hauteur = height or max(len(labels) * 26 + 40, 140)

    # La tige est un trait fin en teinte atténuée : elle guide l'œil du libellé
    # au point sans peser autant qu'une barre.
    teintes = [
        SERIES[0] if (highlight is None or nom == highlight) else INK["deemphasis"]
        for nom in labels
    ]
    pleines = [
        SERIES[0] if (highlight is None or nom == highlight) else INK["muted"]
        for nom in labels
    ]

    fig = go.Figure()

    for index, (nom, valeur) in enumerate(zip(labels, values)):
        fig.add_shape(
            type="line", x0=0, x1=valeur, y0=index, y1=index,
            line=dict(color=teintes[index], width=2.5),
            layer="below",
        )

    fig.add_trace(go.Scatter(
        x=values, y=list(range(len(labels))),
        mode="markers+text",
        marker=dict(size=11, color=pleines,
                    line=dict(color=INK["surface"], width=2)),
        text=[f"  {_fr(v, decimals)}{unit}" for v in values],
        textposition="middle right",
        textfont=dict(size=11, color=INK["secondary"]),
        hovertemplate="%{customdata}<br><b>%{x:,}</b>" + unit + "<extra></extra>",
        customdata=labels,
        cliponaxis=False,
    ))

    fig.update_layout(
        **_base_layout(hauteur),
        # De la place à droite pour l'étiquette de valeur, sinon elle sort du
        # cadre sur la ligne la plus longue.
        xaxis=dict(**_axis(show_grid=False), range=[0, max(values) * 1.22],
                   visible=False),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(len(labels))),
            ticktext=labels,
            tickfont=dict(size=11, color=INK["secondary"]),
            showgrid=False, zeroline=False, showline=False,
            range=[-0.7, len(labels) - 0.3],
        ),
    )

    _show(fig)


def pentes_appariees(df, entite, gauche, droite, titre_gauche="",
                     titre_droite="", unit_gauche="", unit_droite="",
                     max_rows=16, height=None, decimals=1, highlight=None):
    """Deux classements reliés — RELATION entre deux ordres.

    À gauche un rang, à droite un autre, et une courbe par entité. La forme dit
    en un regard ce que deux graphes côte à côte ne disent jamais : QUI change
    de place, et de combien. Un croisement plat signale deux classements
    identiques ; un faisceau croisé, deux critères qui se contredisent.

    C'est la forme du tableau de bord « Searching for a hospital » : population
    d'un côté, équipements pour 10 000 habitants de l'autre. Elle n'a pas
    d'équivalent en barres, parce qu'aucune barre ne relie deux échelles.

    Les deux colonnes portent des UNITÉS différentes : on ne compare donc que
    des RANGS, jamais les valeurs entre elles. Les valeurs restent écrites de
    chaque côté pour que rien ne se lise dans la seule pente.
    """

    data = df[[entite, gauche, droite]].dropna()

    if data.empty:
        return

    data = data.sort_values(gauche, ascending=False).head(max_rows)

    rang_g = data[gauche].rank(ascending=False, method="first")
    rang_d = data[droite].rank(ascending=False, method="first")

    noms = data[entite].astype(str).tolist()
    hauteur = height or max(len(noms) * 30 + 70, 260)

    fig = go.Figure()

    for index, nom in enumerate(noms):
        y0 = float(rang_g.iloc[index])
        y1 = float(rang_d.iloc[index])
        vedette = highlight is not None and nom == highlight
        couleur = SERIES[0] if vedette or highlight is None else INK["deemphasis"]

        # Courbe de Bézier plutôt qu'un segment : à seize entités, seize
        # droites forment un moiré illisible là où des courbes se suivent.
        fig.add_shape(
            type="path",
            path=f"M 0,{y0} C 0.38,{y0} 0.62,{y1} 1,{y1}",
            line=dict(color=couleur, width=2.4 if vedette else 1.6),
            opacity=1 if (highlight is None or vedette) else 0.5,
            layer="below",
        )

    for cote, x, rangs, valeurs, unite, ancrage in (
        ("g", 0.0, rang_g, data[gauche], unit_gauche, "right"),
        ("d", 1.0, rang_d, data[droite], unit_droite, "left"),
    ):
        fig.add_trace(go.Scatter(
            x=[x] * len(noms), y=rangs.tolist(),
            mode="markers+text",
            marker=dict(size=9, color=SERIES[0],
                        line=dict(color=INK["surface"], width=2)),
            text=[
                (f"{nom}  {_fr(v, decimals)}{unite}" if cote == "g"
                 else f"{_fr(v, decimals)}{unite}  {nom}")
                for nom, v in zip(noms, valeurs)
            ],
            textposition="middle left" if cote == "g" else "middle right",
            textfont=dict(size=11, color=INK["secondary"]),
            hoverinfo="skip",
            cliponaxis=False,
        ))

    fig.update_layout(
        **_base_layout(hauteur, margin_l=8),
        xaxis=dict(range=[-0.62, 1.62], visible=False, fixedrange=True),
        # Le rang 1 en HAUT : un classement se lit de haut en bas.
        yaxis=dict(range=[len(noms) + 0.6, 0.4], visible=False, fixedrange=True),
        annotations=[
            dict(x=0, y=0.42, xref="x", yref="paper", text=titre_gauche,
                 showarrow=False, xanchor="center",
                 font=dict(size=11, color=INK["muted"])),
            dict(x=1, y=0.42, xref="x", yref="paper", text=titre_droite,
                 showarrow=False, xanchor="center",
                 font=dict(size=11, color=INK["muted"])),
        ],
    )

    _show(fig)


def petits_multiples(series, colonnes=3, height=150, unit="", decimals=0):
    """Une grille de mini-courbes à ÉCHELLE PARTAGÉE — comparaison de formes.

    L'échelle commune est ce qui fait la forme : sans elle, chaque vignette
    s'auto-normalise et deux séries d'ordres de grandeur opposés paraissent
    identiques. La première et la dernière valeur sont écrites, pour qu'aucune
    lecture ne dépende de l'œil sur un axe de 150 pixels.

    `series` : [{name, x, y}] — même forme que `line_series`.
    """

    if not series:
        return

    toutes = [v for serie in series for v in serie["y"] if v is not None]

    if not toutes:
        return

    bas, haut = min(toutes), max(toutes)
    marge = (haut - bas) * 0.18 or (abs(haut) * 0.1 or 1)

    for depart in range(0, len(series), colonnes):
        cols = st.columns(colonnes, gap="small")

        for col, serie in zip(cols, series[depart:depart + colonnes]):
            with col:
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=list(serie["x"]), y=list(serie["y"]),
                    mode="lines+markers",
                    line=dict(color=SERIES[0], width=2),
                    marker=dict(size=4, color=SERIES[0]),
                    hovertemplate="%{x}<br><b>%{y:,}</b>" + unit + "<extra></extra>",
                ))

                fig.update_layout(
                    **_base_layout(height),
                    title=dict(text=serie["name"], x=0, xanchor="left",
                               font=dict(size=11, color=INK["secondary"])),
                    margin=dict(l=0, r=28, t=26, b=18),
                    xaxis=dict(**_axis(show_grid=False, show_line=True),
                               tickfont=dict(size=9)),
                    yaxis=dict(**_axis(show_grid=True), range=[bas - marge, haut + marge],
                               showticklabels=False),
                    annotations=[
                        dict(x=serie["x"][-1], y=serie["y"][-1], xref="x", yref="y",
                             text=f" {_fr(serie['y'][-1], decimals)}{unit}",
                             showarrow=False, xanchor="left",
                             font=dict(size=10, color=INK["primary"])),
                    ],
                )

                _show(fig, key=f"pm_{serie['name']}")


def _legende_pastilles(labels, couleurs, decalage=0):
    """Légende en pastilles, rendue en HTML plutôt que par plotly.

    Nécessaire pour le demi-anneau : son demi-tour vide est un secteur comme
    un autre pour plotly, qui l'inscrit dans sa légende avec sa valeur — on y
    lisait une troisième catégorie sans nom. Aucun réglage ne masque un seul
    secteur d'un camembert. Les deux anneaux partagent donc cette légende, ce
    qui leur donne aussi la même apparence.
    """

    cases = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:7px;">'
        f'<span style="width:11px;height:11px;border-radius:3px;'
        f'background:{couleur};"></span>'
        f'<span style="font-size:12px;color:{INK["secondary"]};">{libelle}</span>'
        f"</span>"
        for libelle, couleur in zip(labels, couleurs)
    )

    st.markdown(
        f'<div style="display:flex;justify-content:center;flex-wrap:wrap;'
        f'gap:6px 22px;margin:{decalage}px 0 4px;">{cases}</div>',
        unsafe_allow_html=True,
    )


def _parts(valeurs):
    """Parts en pourcentage, somme des valeurs — l'arithmétique d'un anneau."""

    total = float(sum(valeurs))

    if total <= 0:
        return None, 0.0

    return [100 * float(v) / total for v in valeurs], total


def anneau(labels, valeurs, couleurs=None, mise_en_avant=0, height=300,
           trou=0.62, decimals=1, unite="%", legende=True, centre=None,
           sous_centre=None, cle=None, message_vide=None):
    """Anneau — PART D'UN TOUT, et rien d'autre.

    Un anneau ne se lit bien que sur DEUX parts, trois au plus : l'œil compare
    des angles, ce qu'il fait mal, et il ne peut pas ordonner cinq secteurs
    voisins. Au-delà, une barre empilée ou des barres simples disent la même
    chose sans demander d'effort — la fonction laisse faire, mais le choix se
    justifie à chaque fois.

    Ce qui rend celui-ci lisible, et qui manque à la plupart :
      · un seul secteur porte la couleur, les autres restent en gris de
        retrait. `mise_en_avant` désigne son rang. La teinte devient alors un
        VERDICT — « voilà la part qui pose problème » — au lieu d'un simple
        code d'identité que la légende suffirait à donner ;
      · les parts sont écrites en toutes lettres à l'extérieur, dans la
        couleur de leur secteur : sans ça, un anneau se lit à la règle ;
      · le centre est disponible pour le chiffre qui compte (`centre`), là où
        l'œil va spontanément.

    `couleurs` remplace entièrement la palette déduite : une liste de la même
    longueur que `labels`.
    """

    parts, total = _parts(valeurs)

    if parts is None:
        st.info(message_vide or t("commun")("aucun_resultat"))
        return

    if couleurs:
        teintes = list(couleurs)
    else:
        # Emphase : la part désignée en teinte de série, le reste en retrait.
        teintes = [
            SERIES[0] if index == mise_en_avant else INK["deemphasis"]
            for index in range(len(labels))
        ]

    textes = [f"{_fr(p, decimals)}{unite}" for p in parts]

    fig = go.Figure(
        go.Pie(
            labels=list(labels),
            values=list(valeurs),
            hole=trou,
            marker=dict(colors=teintes, line=dict(color=INK["surface"], width=2)),
            text=textes,
            textinfo="text",
            textposition="outside",
            # Chaque étiquette prend la teinte de SON secteur : c'est ce qui
            # dispense de suivre un trait de rappel jusqu'à la légende.
            outsidetextfont=dict(size=13, family=_FONT, color=teintes),
            sort=False,          # l'ordre reçu est un ordre de sens
            direction="clockwise",
            rotation=0,
            hovertemplate="%{label} · %{value:,.0f} (%{percent})<extra></extra>",
        )
    )

    if centre:
        fig.add_annotation(
            text=(f'<span style="font-size:26px;color:{INK["primary"]};">'
                  f"<b>{centre}</b></span>"
                  + (f'<br><span style="font-size:11px;'
                     f'color:{INK["muted"]};">{sous_centre}</span>'
                     if sous_centre else "")),
            x=0.5, y=0.5, showarrow=False, font=dict(family=_FONT),
        )

    fig.update_layout(**_base_layout(height, show_legend=False))
    fig.update_layout(margin=dict(l=44, r=44, t=12, b=12),
                      uniformtext=dict(minsize=11, mode="hide"))

    _show(fig, key=cle)

    # La légende passe SOUS la figure : au-dessus, elle s'intercalait entre le
    # titre de la carte et l'anneau, et se lisait comme un sous-titre.
    if legende:
        _legende_pastilles(labels, teintes)


def demi_anneau(labels, valeurs, couleurs=None, mise_en_avant=0, height=210,
                trou=0.62, decimals=1, unite="%", legende=True, centre=None,
                sous_centre=None, cle=None, message_vide=None):
    """Demi-anneau — même lecture, deux fois moins de hauteur.

    Le demi-cercle n'est pas une variante décorative : à surface d'écran
    égale, il donne un rayon plus grand, donc des secteurs plus lisibles, et
    il laisse le centre libre pour le chiffre. C'est la forme qui convient
    quand la figure doit tenir dans une bande — en tête de page, ou dans une
    colonne déjà chargée.

    Le demi-tour vide est obtenu par un secteur TRANSPARENT de même poids que
    la somme des autres : plotly ne sait pas dessiner un demi-camembert, et
    tourner la figure ne suffirait pas — il faut aussi que le vide n'apparaisse
    ni dans la légende ni au survol.
    """

    parts, total = _parts(valeurs)

    if parts is None:
        st.info(message_vide or t("commun")("aucun_resultat"))
        return

    if couleurs:
        teintes = list(couleurs)
    else:
        teintes = [
            SERIES[0] if index == mise_en_avant else INK["deemphasis"]
            for index in range(len(labels))
        ]

    textes = [f"{_fr(p, decimals)}{unite}" for p in parts]

    fig = go.Figure(
        go.Pie(
            labels=[*labels, ""],
            values=[*valeurs, total],
            hole=trou,
            marker=dict(
                colors=[*teintes, "rgba(0,0,0,0)"],
                line=dict(color=INK["surface"], width=2),
            ),
            text=[*textes, ""],
            textinfo="text",
            textposition="outside",
            outsidetextfont=dict(size=13, family=_FONT,
                                 color=[*teintes, "rgba(0,0,0,0)"]),
            sort=False,
            direction="clockwise",
            # Le demi-tour vide commence à 9 h : les parts occupent alors la
            # moitié HAUTE, celle que l'œil lit en premier.
            rotation=270,
            hovertemplate="%{label} · %{value:,.0f}<extra></extra>",
        )
    )

    if centre:
        fig.add_annotation(
            text=(f'<span style="font-size:24px;color:{INK["primary"]};">'
                  f"<b>{centre}</b></span>"
                  + (f'<br><span style="font-size:11px;'
                     f'color:{INK["muted"]};">{sous_centre}</span>'
                     if sous_centre else "")),
            # Le centre géométrique du camembert est au MILIEU de la figure ;
            # comme seule la moitié haute est peinte, le chiffre se pose juste
            # au-dessus de ce milieu, dans l'ouverture de l'anneau. Placé plus
            # bas, il tombait sous l'arc et se confondait avec la légende.
            x=0.5, y=0.46, yanchor="bottom", showarrow=False,
            font=dict(family=_FONT),
        )

    fig.update_layout(**_base_layout(height, show_legend=False))
    fig.update_layout(margin=dict(l=44, r=44, t=12, b=0),
                      uniformtext=dict(minsize=11, mode="hide"))

    _show(fig, key=cle)

    if legende:
        # Le camembert occupe un carré, dont seule la moitié haute est peinte :
        # la moitié basse reste un blanc que rien ne remplit et qui repoussait
        # la légende à 125 px de l'arc. On la remonte d'autant.
        _legende_pastilles(labels, teintes, decalage=-int(height * 0.40))
