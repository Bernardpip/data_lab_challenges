"""Design tokens — port Python de zendho `kelviGuard_package/styles/tokens.ts`
et des valeurs réelles de `global.css` (`:root`, thème light).

Les .tsx référencent `var(--kg-color-X)` ; ici on résout directement en hex
puisqu'il n'y a qu'un thème (light) — les CSS custom properties sont quand
même émises par `styles.py` pour que les composants HTML les consomment.
"""

# ─── Couleurs (global.css `:root` / [data-theme="light"]) ────────────────────

COLORS = {
    # Brand
    "primary": "#6366F1",
    "primaryHover": "#4F46E5",
    "primaryLight": "#EEF2FF",
    "primaryDark": "#4338CA",

    # Semantic
    "success": "#10B981",
    "successLight": "#D1FAE5",
    "successDark": "#059669",
    "warning": "#F59E0B",
    "warningLight": "#FEF3C7",
    "warningDark": "#B45309",
    "error": "#EF4444",
    "errorLight": "#FEE2E2",
    "errorDark": "#DC2626",
    "info": "#3B82F6",
    "infoLight": "#DBEAFE",
    "infoDark": "#2563EB",

    # Neutral
    "white": "#FFFFFF",
    "background": "#F0F0F0",
    "surface": "#FCFCFC",
    "surfaceHover": "#F0F0F0",
    "surfaceActive": "#E8E8E8",
    "surfaceSecondary": "#F1F5F9",

    # Sidebar
    "sidebar": "#0F172A",
    "sidebarHover": "#1E293B",
    "sidebarActive": "rgba(99, 102, 241, 0.15)",
    "sidebarText": "#94A3B8",
    "sidebarTextActive": "#FFFFFF",
    "sidebarSection": "#64748B",
    "sidebarBorder": "rgba(255, 255, 255, 0.06)",

    # Text
    "text": "#0F172A",
    "textSecondary": "#475569",
    "textMuted": "#94A3B8",
    "textOnPrimary": "#FFFFFF",

    # Borders
    "border": "#E0E0E0",
    "borderLight": "#EBEBEB",
    "borderHover": "#CECECE",
    "borderFocus": "#6366F1",

    # Accents
    "link": "#0469C1",
    "linkHover": "#024F94",
    "violet": "#8B5CF6",
    "pink": "#EC4899",
    "gray": "#6B7280",

    # Neutrals (mapping ~tailwind slate/gray)
    "neutral50": "#F9FAFB",
    "neutral100": "#F3F4F6",
    "neutral200": "#E5E7EB",
    "neutral300": "#D1D5DB",
    "neutral400": "#9CA3AF",
    "neutral500": "#6B7280",
    "neutral600": "#4B5563",
    "neutral700": "#374151",
    "neutral800": "#1F2937",
    "neutral900": "#111827",

    # Pills
    "pillActiveBg": "#D1FAE5",
    "pillActiveFg": "#059669",
    "pillInactiveBg": "#FEE2E2",
    "pillInactiveFg": "#DC2626",
    "pillDeprecatedBg": "#FEF3C7",
    "pillDeprecatedFg": "#B45309",
    "pillDraftBg": "#F1F5F9",
    "pillDraftFg": "#475569",
}


SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "20px",
    "2xl": "24px",
    "3xl": "32px",
    "4xl": "40px",
    "5xl": "48px",
}

RADII = {
    "sm": "4px",
    "md": "6px",
    "lg": "8px",
    "xl": "12px",
    "2xl": "16px",
    "full": "9999px",
}

SHADOWS = {
    "xs": "0 1px 1px rgba(0, 0, 0, 0.04)",
    "sm": "0 1px 3px rgba(0, 0, 0, 0.06)",
    "md": "0 1px 8px rgba(0, 0, 0, 0.08)",
    "lg": "0 4px 16px rgba(0, 0, 0, 0.1)",
    "xl": "0 8px 24px rgba(0, 0, 0, 0.12)",
}

TYPOGRAPHY = {
    "fontFamily": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
                  '"Helvetica Neue", Arial, sans-serif',
    "fontMono": '"SF Mono", "Fira Code", "Cascadia Code", "JetBrains Mono", monospace',
    "fontSize": {
        "xxs": "10px",
        "xs": "12px",
        "sm": "12px",
        "base": "13px",
        "lg": "14px",
        "xl": "16px",
        "2xl": "18px",
        "3xl": "22px",
        "4xl": "28px",
    },
    "fontWeight": {
        "extra_small": "100",
        "small": "200",
        "normal": "400",
        "medium": "500",
        "semibold": "600",
        "bold": "700",
    },
    "lineHeight": {"tight": "1.25", "normal": "1.5", "relaxed": "1.625"},
}

LAYOUT = {
    "sidebarWidth": 240,
    "sidebarCollapsedWidth": 60,
    "topBarHeight": 48,
    "tabBarHeight": 36,
    "tableRowHeight": 40,
}

TRANSITIONS = {"fast": "120ms ease", "normal": "200ms ease", "slow": "300ms ease"}


# ─── Palette data-viz ────────────────────────────────────────────────────────
# Palette de référence de la méthode dataviz, VALIDÉE sur la surface zendho
# (#FCFCFC) via scripts/validate_palette.js :
#   · adjacente (barres/lignes/empilements) : 8 slots, worst CVD ΔE 9.1,
#     worst normal-vision ΔE 19.6 → tous les gates passent.
#   · all-pairs (scatter/carte/small multiples) : plafonné aux 3 premiers slots.
#   · WARN contraste < 3:1 sur les slots aqua/jaune/magenta → règle de relief :
#     ces charts embarquent labels directs + vue tableau (jamais couleur seule).
# Les couleurs de marque zendho (primary indigo…) restent au CHROME (boutons,
# onglets) : elles n'encodent jamais une série.

SERIES = [
    "#2a78d6",  # 1 · bleu
    "#eb6834",  # 2 · orange
    "#1baf7a",  # 3 · aqua
    "#eda100",  # 4 · jaune
    "#e87ba4",  # 5 · magenta
    "#008300",  # 6 · vert
    "#4a3aa7",  # 7 · violet
    "#e34948",  # 8 · rouge
]

# Nombre max de séries en forme « all-pairs » (nuage de points, carte,
# small multiples) — au-delà : replier en « Autre » ou facetter.
SERIES_ALLPAIRS_CAP = 3

# Séquentiel continu (magnitude) — une seule teinte, clair→foncé.
SEQUENTIAL = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]

# Ordinal discret (paliers ordonnés) — validé `--ordinal` : L monotone,
# ΔL ≥ 0.06, extrémité claire à 2.06:1 sur #FCFCFC.
ORDINAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]

# Divergent : deux pôles chaud/froid + gris neutre au milieu.
DIVERGING = {"neg": "#e34948", "mid": "#f0efec", "pos": "#2a78d6"}

# ─── Rampes de PRODUCTEUR ────────────────────────────────────────────────────
# Certaines institutions publient leurs cartes avec une rampe imposée. La
# reprendre n'est pas une coquetterie : un tableau de bord qui recolore une
# carte officielle oblige son lecteur à réapprendre une lecture qu'il connaît
# déjà, et fait douter qu'il s'agisse bien de la même donnée.
#
# RISQUE — ColorBrewer RdYlGn à 5 classes, inversée. Relevée au pixel sur les
# cartes publiées avec les indices FSI/FRI du Togo (opendata.gouv.tg).
#
# ⚠ Cette rampe est ROUGE-VERT : ses deux extrémités sont indistinguables pour
# une deutéranopie ou une protanopie, soit environ 8 % des hommes. Elle n'est
# donc admise que là où la valeur reste atteignable AUTREMENT — infobulle et
# `table_twin()` obligatoires, ce que le socle impose déjà pour toute carte.
# Ne jamais l'employer comme palette catégorielle : elle encode un ORDRE.
RISQUE_OFFICIEL = ["#1a9641", "#a6d96a", "#ffffc0", "#fdae61", "#d7191c"]

# Le fond noir des cartes du producteur. Le tableau de bord reste en thème
# clair : seul le liseré entre polygones s'en inspire, pour que les classes
# claires ne fusionnent pas avec la surface de la page.
RISQUE_CONTOUR = "#232323"

# Statut (réservé, jamais réutilisé comme série ; toujours icône + libellé).
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

# Les mêmes, en SURFACE. Un statut porté par la seule couleur d'un mot se voit
# mal dans une rangée de tuiles : l'œil parcourt les grands chiffres et saute
# la ligne de détail. Une teinte de fond fait lire le statut avant le chiffre.
#
# Assez claires pour qu'un texte d'encre reste à plus de 12:1 dessus : ce sont
# des FONDS, jamais de l'encre, et rien d'autre ne doit s'y écrire en couleur.
STATUS_LIGHT = {
    "good": "#E8F5E9",
    "warning": "#FDF6DF",
    "serious": "#FCEEE7",
    "critical": "#FBEBEB",
}

# Encre & chrome des graphes — repris des tokens zendho pour que le chart
# s'assoie dans l'UI sans jurer.
INK = {
    "surface": COLORS["surface"],
    "primary": COLORS["text"],
    "secondary": COLORS["textSecondary"],
    "muted": COLORS["textMuted"],
    "grid": COLORS["borderLight"],
    "axis": COLORS["border"],
    "deemphasis": COLORS["neutral300"],
}
