"""Feuille de style globale — port Python de `kelviGuard_package/styles/global.css`
plus les surcharges nécessaires pour que les widgets Streamlit adoptent la
densité zendho (base 13px, hairlines, marques fines).

Même mécanique que le CSS d'origine : les tokens sont émis en CSS custom
properties `--kg-*`, et tout le corps de la feuille ne consomme que ces
variables (aucun hex en dur ici).
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from socle.design.tokens import COLORS, LAYOUT, TYPOGRAPHY


def _vars(sidebar_width):
    """Bloc `:root` — équivalent des `--kg-color-*` de global.css."""

    def kebab(name):
        out = ""
        for ch in name:
            out += "-" + ch.lower() if ch.isupper() else ch
        return out

    lines = [f"  --kg-color-{kebab(k)}: {v};" for k, v in COLORS.items()]
    lines += [
        f"  --kg-font: {TYPOGRAPHY['fontFamily']};",
        f"  --kg-font-mono: {TYPOGRAPHY['fontMono']};",
        f"  --kg-fs-xxs: {TYPOGRAPHY['fontSize']['xxs']};",
        f"  --kg-fs-xs: {TYPOGRAPHY['fontSize']['xs']};",
        f"  --kg-fs-base: {TYPOGRAPHY['fontSize']['base']};",
        f"  --kg-fs-lg: {TYPOGRAPHY['fontSize']['lg']};",
        f"  --kg-fs-xl: {TYPOGRAPHY['fontSize']['xl']};",
        f"  --kg-fs-2xl: {TYPOGRAPHY['fontSize']['2xl']};",
        f"  --kg-fs-3xl: {TYPOGRAPHY['fontSize']['3xl']};",
        f"  --kg-fs-4xl: {TYPOGRAPHY['fontSize']['4xl']};",
        f"  --kg-topbar-h: {LAYOUT['topBarHeight']}px;",
        f"  --kg-tabbar-h: {LAYOUT['tabBarHeight']}px;",
        f"  --kg-sidebar-w: {sidebar_width}px;",
        # Vert du drapeau togolais — couleur nationale, hors palette zendho.
        "  --kg-togo-green: #006A4E;",
        # Rouge du lion Data AI Lab — couleur de marque du laboratoire.
        "  --kg-lab-red: #C8213C;",
    ]
    return ":root {\n" + "\n".join(lines) + "\n}"


# Corps statique : uniquement des var(--kg-*), jamais d'hex.
_CSS = """
/* ─── Base ──────────────────────────────────────────────────────────────── */

html, body, [data-testid="stAppViewContainer"] {
  font-family: var(--kg-font);
  font-size: var(--kg-fs-base);
  color: var(--kg-color-text);
  background-color: var(--kg-color-background);
}

/* Chrome Streamlit retiré : le shell fournit sa propre top bar. */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebarNav"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarHeader"],
footer { display: none !important; }

/* Le bas de page réserve la hauteur du footer fixe, sinon le dernier
   élément passerait dessous. */
[data-testid="stMainBlockContainer"] {
  padding: 0 24px 52px 24px;
  max-width: 100%;
}

/* `load_styles()` injecte sa feuille via `st.markdown`, ce qui crée un
   conteneur d'élément INVISIBLE mais bien présent dans le flux : le bloc
   vertical lui applique quand même son `gap`, d'où 24px de vide au-dessus du
   header. `display:none` le sort de la mise en page — la balise <style>
   qu'il contient continue de s'appliquer (une feuille agit quel que soit
   l'affichage de son parent). */
[data-testid="stElementContainer"]:has(style) { display: none !important; }

/* Rythme vertical. Deux cartes à bordure fine et fond quasi blanc, l'une sous
   l'autre, se lisent comme collées en dessous de ~16px — il faut un vrai
   espace de respiration entre deux BLOCS (rangée de tuiles, rangée de
   cartes), tout en restant plus serré à l'intérieur d'un même bloc. */
[data-testid="stVerticalBlock"] { gap: 10px; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 24px; }
[data-testid="stHorizontalBlock"] { gap: 16px; }

/* Repli des colonnes sur écran étroit.
   Streamlit garde ses colonnes côte à côte quelle que soit la largeur et les
   comprime indéfiniment. On autorise le retour à la ligne, avec un plancher
   VOLONTAIREMENT BAS : à 160px, rien ne bouge aux largeurs courantes — un
   seuil plus haut faisait passer une rangée de quatre tuiles sur deux lignes
   dès 1 440px, ce qui dégradait l'affichage au lieu de l'améliorer. Le repli
   ne se déclenche donc que sur les écrans réellement étroits, où la
   compression rendrait le contenu illisible de toute façon. */
[data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 160px; }

/* La barre de filtres fait exception : ses contrôles tiennent sur deux unités
   de grille (1/6) et doivent le rester, sinon un seul filtre occuperait une
   ligne entière.

   Son écart est ramené à 12px, et ce n'est pas une question d'esthétique.
   Streamlit dimensionne chaque colonne en `calc(<part>% - 13px)` : le 13px
   est sa PROVISION D'ÉCART, codée en dur. Notre écart global de 16px la
   dépasse de 3px par intervalle — sans conséquence tant qu'une rangée compte
   peu de colonnes, mais la barre territoriale en porte six (cinq filtres plus
   la colonne d'appui), soit 5 × 3px de trop : la somme franchissait 100 % et
   la dernière colonne PASSAIT À LA LIGNE, où, seule, elle s'étirait sur toute
   la largeur. Sous la provision de Streamlit, l'arithmétique retombe juste
   quel que soit le nombre de colonnes. */
[data-testid="stHorizontalBlock"]:has([data-testid="stMultiSelect"]),
[data-testid="stHorizontalBlock"]:has([data-testid="stSlider"]) { gap: 12px; }

[data-testid="stHorizontalBlock"]:has([data-testid="stMultiSelect"]) >
[data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has([data-testid="stSlider"]) >
[data-testid="stColumn"] { min-width: 150px; }

/* ── Listes à choix multiples ──────────────────────────────────────────────
   Le contrôle natif empile une pastille par ligne quand la largeur ne permet
   pas de les mettre côte à côte : cinq villes retenues faisaient grandir la
   barre de filtres sur cinq lignes et repoussaient le graphe hors de l'écran.
   Un filtre ne doit pas changer la HAUTEUR de la page selon ce qu'on y coche.

   La correction tient en deux points : des pastilles compactes (deux tiennent
   alors sur une ligne à 1/6 de large), et une hauteur PLAFONNÉE à trois
   rangées au-delà desquelles le contrôle défile en interne. On garde ainsi la
   sélection entièrement consultable — la masquer derrière un « +3 » obligerait
   à ouvrir le menu pour savoir ce qui est filtré. */
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child {
  max-height: 96px;
  overflow-y: auto;
  align-items: flex-start;
  scrollbar-width: thin;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] {
  height: 22px;
  margin: 2px 2px 0 0;
  padding-left: 8px;
  border-radius: 5px;
  max-width: 100%;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span {
  font-size: var(--kg-fs-xs);
  line-height: 1.2;
}
/* Un libellé long est tronqué, pas replié : « Formation professionnelle
   (autre) » ferait sinon une pastille de trois lignes à lui seul. */
[data-testid="stMultiSelect"] [data-baseweb="tag"] > span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Anneau de focus ───────────────────────────────────────────────────────
   Le champ à choix multiples garde un <input> de DEUX PIXELS de large tant
   qu'on n'y a rien tapé — il ne sert qu'à la saisie, la valeur vit dans les
   pastilles. L'anneau de focus dessiné dessus se réduisait donc à ses deux
   côtés verticaux : deux petits traits violets collés au bord gauche du
   champ, sans rapport visible avec quoi que ce soit. Ses côtés haut et bas
   existaient bien, mais longs de deux pixels.

   L'anneau est déplacé sur la surface VISIBLE du contrôle. Il n'est pas
   supprimé : sans lui, un parcours au clavier ne montrerait plus où il en
   est. */
[data-testid="stMultiSelect"] input:focus,
[data-testid="stMultiSelect"] input:focus-visible { outline: none; }

[data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within {
  border-color: var(--kg-color-border-focus);
  box-shadow: 0 0 0 3px color-mix(in srgb,
              var(--kg-color-border-focus) 18%, transparent);
}

/* Sécurité indépendante du gap flex parent (qu'une structure de colonnes
   imbriquée peut réduire) : chaque carte porte aussi sa propre marge. */
.kg-card,
[class*="st-key-kgcard"] { margin-top: 8px; }

h1, h2, h3, h4 {
  font-family: var(--kg-font);
  color: var(--kg-color-text);
  letter-spacing: -0.01em;
  margin: 0;
  padding: 0;
}
h1 { font-size: var(--kg-fs-3xl); font-weight: 600; }
h2 { font-size: var(--kg-fs-2xl); font-weight: 600; }
h3 { font-size: var(--kg-fs-lg);  font-weight: 600; }

p, li, label, span, div { font-size: var(--kg-fs-base); }

hr { border-color: var(--kg-color-border-light); margin: 10px 0; }

/* Le fil d'Ariane reste en HTML (pas de navigation) : on lui retire seulement
   le soulignement que Streamlit applique aux liens de contenu. */
.kg-crumb { text-decoration: none !important; }
[data-testid="stMarkdownContainer"] .kg-crumb { color: var(--kg-color-text-muted); }
[data-testid="stMarkdownContainer"] .kg-crumb:hover { color: var(--kg-color-text); }

/* ─── Sidebar (SlideBar.tsx) ────────────────────────────────────────────── */

[data-testid="stSidebar"] {
  width: var(--kg-sidebar-w) !important;
  min-width: var(--kg-sidebar-w) !important;
  background-color: var(--kg-color-sidebar);
  border-right: none;
  transition: width 200ms ease;
}
[data-testid="stSidebar"] > div { background-color: var(--kg-color-sidebar); }
[data-testid="stSidebar"] > div:first-child { height: 100%; }
[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] { gap: 0; }

/* `stSidebarContent` (natif Streamlit, un cran AU-DESSUS de
   `stSidebarUserContent`) porte un padding fixe de 16,25px de chaque côté.
   Invisible sur 240px de large ; sur 60px en mode réduit, ça mangeait plus de
   la moitié de la largeur — d'où les icônes décentrées et tronquées. Chaque
   élément (header, boutons) gère déjà son propre padding, donc ce
   conteneur-là n'en a plus besoin. */
[data-testid="stSidebarContent"] { padding-left: 0; padding-right: 0; }

/* Header : wordmark aligné à gauche (étendu) / icône centrée (réduit). */
.kg-sb-header {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1px;
  height: var(--kg-topbar-h);
  padding: 0 16px 0 18px;
  border-bottom: 1px solid var(--kg-color-sidebar-border);
  color: var(--kg-color-sidebar-text-active);
  white-space: nowrap;
  overflow: hidden;
  box-sizing: border-box;
}
.kg-sb-header.collapsed {
  align-items: center;
  justify-content: center;
  padding: 0;
}
.kg-sb-wordmark {
  font-size: var(--kg-fs-lg);
  font-weight: 700;
  letter-spacing: 0.14em;
  line-height: 1.1;
}
.kg-sb-byline {
  font-size: var(--kg-fs-xxs);
  font-weight: 500;
  letter-spacing: 0.12em;
  color: var(--kg-color-sidebar-text);
  line-height: 1.1;
}

/* La sidebar est une colonne pleine hauteur : header, puis la nav qui prend
   tout l'espace disponible (`flex:1`), puis le contrôle qui se retrouve donc
   naturellement en bas — exactement le montage de SlideBar.tsx.
   Streamlit empile la sidebar dans des conteneurs `display:block` : il faut
   les passer en flex un par un, sinon la nav n'a aucune hauteur à occuper.
   (Un `position:fixed` a été essayé puis abandonné : il sortait le bloc du
   flux, d'où un bouton désaligné des entrées de nav et des recouvrements.) */
[data-testid="stSidebarUserContent"] {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 0;
}
[data-testid="stSidebarUserContent"] > div {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}
[data-testid="stSidebarUserContent"] [data-testid="stLayoutWrapper"]:has([class*="st-key-kgsbnav"]) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

[class*="st-key-kgsbnav"] {
  gap: 0;
  flex: 1;
  padding: 10px 0;
  overflow-y: auto;
  scrollbar-width: none;
}
[class*="st-key-kgsbnav"]::-webkit-scrollbar { display: none; }

[class*="st-key-kgsbctrl"] {
  flex-shrink: 0;
  padding: 6px 0;
  border-top: 1px solid var(--kg-color-sidebar-border);
}

/* Entrées de nav : des boutons Streamlit remis à l'apparence des NavLink du
   .tsx — bordure gauche 4px transparente qui passe en indigo quand la section
   est active (`type="primary"`). */
[data-testid="stSidebar"] .stButton button {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 8px 12px 8px 14px;
  background-color: transparent;
  border: none;
  border-left: 4px solid transparent;
  border-radius: 0;
  color: var(--kg-color-sidebar-text);
  font-family: var(--kg-font);
  font-size: var(--kg-fs-base);
  font-weight: 400;
  min-height: 36px;
  white-space: nowrap;
  overflow: hidden;
  transition: 120ms ease;
  box-shadow: none;
}
/* La couleur doit être forcée sur le bouton ET sur ses enfants (le libellé
   est dans un <p>, l'icône dans un <span> Material) : le thème Streamlit
   applique `textColor` — sombre — aux boutons `tertiary`, ce qui rendait le
   texte et les icônes NOIRS SUR FOND NOIR, donc invisibles. */
[data-testid="stSidebar"] .stButton button,
[data-testid="stSidebar"] .stButton button p,
[data-testid="stSidebar"] .stButton button span {
  color: var(--kg-color-sidebar-text) !important;
}
[data-testid="stSidebar"] .stButton button:hover {
  background-color: var(--kg-color-sidebar-hover);
  border-left-color: transparent;
}
[data-testid="stSidebar"] .stButton button:hover,
[data-testid="stSidebar"] .stButton button:hover p,
[data-testid="stSidebar"] .stButton button:hover span,
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[kind="primary"] p,
[data-testid="stSidebar"] .stButton button[kind="primary"] span {
  color: var(--kg-color-sidebar-text-active) !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
  background-color: var(--kg-color-sidebar-active);
  border-left-color: var(--kg-color-primary);
  font-weight: 500;
}
[data-testid="stSidebar"] .stButton button:focus,
[data-testid="stSidebar"] .stButton button:active {
  box-shadow: none;
  outline: none;
}

/* Sélecteur de langue — en pied, au-dessus du contrôle de repli.
   Ses boutons ne sont PAS des entrées de navigation : ils portent un code de
   deux lettres et doivent se lire comme une bascule. On annule donc
   l'alignement à gauche et la bordure d'onglet actif hérités de la nav, au
   profit d'un libellé centré.

   Forme retenue : un CONTRÔLE SEGMENTÉ — un seul rail arrondi contenant les
   deux langues, l'active portée par une pastille claire qui se détache du
   rail. Deux rectangles voisins, dont l'un rempli d'indigo sur un fond déjà
   bleu nuit, ne se lisaient pas comme une bascule : l'indigo se confondait
   avec la barre et l'ensemble ressemblait à deux boutons distincts. Le rail
   dit « ces deux-là sont les faces d'un même réglage », et le contraste
   clair/sombre dit laquelle est retenue sans dépendre d'une teinte.

   CE BLOC DOIT RESTER APRÈS CELUI DES ENTRÉES DE NAV. Les deux visent des
   boutons de la barre latérale à spécificité ÉGALE, donc c'est l'ordre du
   fichier qui tranche : écrit plus haut, le rail se faisait écraser par le
   `border-radius: 0` et le fond actif de la nav — la pastille redevenait un
   rectangle indigo sans qu'aucune règle ne soit fausse pour autant. */
[class*="st-key-kgsblang"] {
  flex-shrink: 0;
  padding: 10px 12px 4px;
  border-top: 1px solid var(--kg-color-sidebar-border);
}
/* Le rail. `has()` vise la rangée de colonnes en mode déplié ; en mode replié
   il n'y a qu'un bouton, traité plus bas. */
[class*="st-key-kgsblang"] [data-testid="stHorizontalBlock"] {
  gap: 2px;
  flex-wrap: nowrap;
  padding: 3px;
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 999px;
}
/* Exemption au plancher de 160px posé plus haut sur les colonnes : la barre
   latérale ne fait que 240px, donc deux colonnes à 160px se replieraient l'une
   sous l'autre et le sélecteur ressemblerait à deux entrées de navigation. */
[class*="st-key-kgsblang"] [data-testid="stHorizontalBlock"] >
[data-testid="stColumn"] {
  min-width: 0;
}
[class*="st-key-kgsblang"] .stButton button {
  justify-content: center;
  gap: 0;
  padding: 3px 0;
  min-height: 24px;
  background-color: transparent;
  border: none;
  border-left: none;
  border-radius: 999px;
  color: var(--kg-color-sidebar-text);
  font-size: var(--kg-fs-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  transition: background-color 120ms ease, color 120ms ease;
}
[class*="st-key-kgsblang"] .stButton button:hover {
  background-color: rgba(255, 255, 255, 0.06);
}
/* La langue active : une pastille CLAIRE posée sur le rail sombre — la même
   logique d'élévation que les contrôles segmentés du système. L'ombre portée
   est ce qui la fait lire comme « au-dessus » plutôt que « coloriée ». */
[class*="st-key-kgsblang"] .stButton button[kind="primary"],
[class*="st-key-kgsblang"] .stButton button[kind="primary"]:hover {
  background-color: rgba(255, 255, 255, 0.14);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.35),
              inset 0 1px 0 rgba(255, 255, 255, 0.10);
  border: none;
}
[class*="st-key-kgsblang"] .stButton button[kind="primary"] p,
[class*="st-key-kgsblang"] .stButton button[kind="primary"] span {
  color: #FFFFFF !important;
}
/* Replié : il n'y a qu'un bouton, donc pas de rangée de colonnes à habiller —
   le bouton porte lui-même le rail, pour que la bascule garde la même forme
   d'un état de barre à l'autre. */
[class*="st-key-kgsblang-collapsed"] { padding: 10px 8px 4px; }
[class*="st-key-kgsblang-collapsed"] .stButton button {
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.07);
  min-height: 28px;
}

[data-testid="stSidebar"] .stButton button p { font-size: var(--kg-fs-base); }
[data-testid="stSidebar"] .stButton button span[data-testid="stIconMaterial"] {
  font-size: 19px;
}

/* Réduit : le padding asymétrique du mode étendu (14px gauche / 12px droite,
   pensé pour icône + libellé) ne laissait quasi plus de largeur à l'icône
   SEULE dans un bouton de 60px de rail — elle apparaissait tronquée à un
   éclat de trait. Padding symétrique + icône centrée. */
[class*="st-key-kgsbnav-collapsed"] .stButton button,
[class*="st-key-kgsbctrl-collapsed"] .stButton button {
  justify-content: center;
  padding: 8px 0;
}

/* ─── Top bar + fil d'Ariane (MainContainer.tsx) ────────────────────────── */

/* Fil d'Ariane et barre d'onglets restent FIXES au défilement : seul le
   contenu bouge, comme dans le shell zendho.
   Le `position:sticky` est porté par le CONTENEUR Streamlit, pas par la barre
   elle-même : un élément sticky ne colle qu'à l'intérieur des limites de son
   parent, et ici chaque parent (stElementContainer / stLayoutWrapper) fait
   exactement la hauteur de son contenu — la barre défilait donc avec lui.
   Posé sur le conteneur, qui est enfant direct du bloc vertical couvrant
   toute la page, le collage fonctionne. */
[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:has(.kg-topbar) {
  position: sticky;
  top: 0;
  z-index: 112;
}
[data-testid="stMainBlockContainer"] [data-testid="stLayoutWrapper"]:has(> [class*="st-key-kgtabs"]) {
  position: sticky;
  top: var(--kg-topbar-h);  /* juste sous le fil d'Ariane épinglé */
  z-index: 111;
}

.kg-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--kg-topbar-h);
  margin: 0 -24px;
  padding: 0 24px;
  background-color: var(--kg-color-surface);
  border-bottom: 1px solid var(--kg-color-border-light);
  box-shadow: 0 1px 1px rgba(15, 23, 42, 0.03);
}
.kg-crumbs {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--kg-fs-sm);
  color: var(--kg-color-text-muted);
}
.kg-crumb {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--kg-color-text-muted);
  text-decoration: none;
}
.kg-crumb:hover { color: var(--kg-color-text); }
.kg-crumb-sep { display: inline-flex; color: var(--kg-color-border); margin: 0 4px; }
.kg-crumb-current { color: var(--kg-color-text); font-weight: 600; }

/* Tête du fil d'Ariane : 🇹🇬 République togolaise, en vert du drapeau. */
.kg-crumb-org {
  font-weight: 600;
  color: var(--kg-togo-green);
}
.kg-crumb-org:hover { color: var(--kg-togo-green); }
.kg-topbar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--kg-color-text-muted);
  white-space: nowrap;
  text-decoration: none;
  border-radius: 6px;
  padding: 4px 6px;
  margin: -4px -6px;
  transition: 120ms ease;
}
.kg-topbar-brand:hover {
  background-color: var(--kg-color-background);
  color: var(--kg-color-text);
}
/* Logo Data AI Lab : lion ROUGE, texte NOIR — couleurs de la marque, qui ne
   suivent donc pas l'encre muted de la barre. */
.kg-topbar-brand-icon { color: var(--kg-lab-red); display: flex; }
.kg-topbar-brand:hover .kg-topbar-brand-icon { color: var(--kg-lab-red); }
.kg-topbar-brand-text {
  color: var(--kg-color-text);
  font-size: var(--kg-fs-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  line-height: 1.15;
}

/* ─── Barre d'onglets (SectionTabs.tsx) ─────────────────────────────────── */

/* Le conteneur des onglets EST le bloc vertical Streamlit : on le remet en
   ligne pour retrouver la barre horizontale du .tsx.
   Le `position:sticky` n'est PAS ici : il est sur son `stLayoutWrapper`
   parent (règle plus haut). Un sticky posé ICI EN PLUS, combiné aux marges
   négatives de bord-à-bord, tronquait la largeur de la barre (sticky imbriqué
   dans un sticky déjà actif — largeur mal recalculée par le navigateur). */
[class*="st-key-kgtabs"] {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 0;
  min-height: var(--kg-tabbar-h);
  /* Bord-à-bord : les marges négatives seules ne suffisaient pas — Streamlit
     fixe une largeur explicite sur ce bloc, donc `margin-right:-24px` le
     décalait sans l'élargir (d'où une barre tronquée de 48px à droite).
     La largeur est recalculée explicitement pour absorber les deux marges. */
  width: calc(100% + 48px) !important;
  max-width: none !important;
  margin: 0 -24px 4px -24px;
  padding: 0 16px;
  background-color: var(--kg-color-surface);
  border-bottom: 1.5px solid var(--kg-color-primary);
}
[class*="st-key-kgtabs"] > [data-testid="stElementContainer"] {
  width: auto;
  flex: 0 0 auto;
}

[class*="st-key-kgtabs"] .stButton button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: var(--kg-tabbar-h);
  min-height: var(--kg-tabbar-h);
  padding: 0 12px;
  background-color: transparent;
  border: none;
  border-top: 3px solid transparent;
  border-bottom: 1px solid var(--kg-color-neutral-400);
  border-radius: 0;
  color: var(--kg-color-text);
  font-family: var(--kg-font);
  font-size: var(--kg-fs-sm);
  font-weight: 500;
  white-space: nowrap;
  transition: 120ms ease;
  box-shadow: none;
}
[class*="st-key-kgtabs"] .stButton button,
[class*="st-key-kgtabs"] .stButton button p,
[class*="st-key-kgtabs"] .stButton button span {
  color: var(--kg-color-text-secondary) !important;
}
[class*="st-key-kgtabs"] .stButton button:hover {
  background-color: var(--kg-color-background);
}
[class*="st-key-kgtabs"] .stButton button:hover,
[class*="st-key-kgtabs"] .stButton button:hover p,
[class*="st-key-kgtabs"] .stButton button:hover span,
[class*="st-key-kgtabs"] .stButton button[kind="primary"],
[class*="st-key-kgtabs"] .stButton button[kind="primary"] p,
[class*="st-key-kgtabs"] .stButton button[kind="primary"] span {
  color: var(--kg-color-primary) !important;
}
[class*="st-key-kgtabs"] .stButton button[kind="primary"],
[class*="st-key-kgtabs"] .stButton button[kind="primary"]:hover {
  border-top-color: var(--kg-color-primary);
  background-color: var(--kg-color-primary-light);
}
[class*="st-key-kgtabs"] .stButton button:focus,
[class*="st-key-kgtabs"] .stButton button:active {
  box-shadow: none;
  outline: none;
}
[class*="st-key-kgtabs"] .stButton button p { font-size: var(--kg-fs-sm); }
[class*="st-key-kgtabs"] .stButton button span[data-testid="stIconMaterial"] {
  font-size: 16px;
}

/* ─── Carte de contenu (le bloc « Profiles » des écrans zendho) ─────────── */

.kg-card,
[class*="st-key-kgcard"] {
  background-color: var(--kg-color-surface);
  border: 1px solid var(--kg-color-border-light);
  border-radius: 8px;
  padding: 14px 16px 12px 16px;
}

.kg-card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}
.kg-card-title { font-size: var(--kg-fs-xl); font-weight: 600; color: var(--kg-color-text); }
.kg-card-sub {
  font-size: var(--kg-fs-xs);
  color: var(--kg-color-text-muted);
  margin-top: 2px;
  font-weight: 400;
}
.kg-card-note {
  font-size: var(--kg-fs-xs);
  color: var(--kg-color-text-secondary);
  border-left: 2px solid var(--kg-color-primary);
  padding-left: 10px;
  margin: 2px 0 10px 0;
  line-height: 1.55;
}

/* Repère de contexte EXTERNE (INSEED, Afrobarometer…) : fond ambré pour se
   distinguer d'une conclusion tirée des données du portail. */
.kg-context {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 14px;
  margin: 8px 0;
  border: 1px solid var(--kg-color-warning-light);
  border-left: 3px solid var(--kg-color-warning);
  border-radius: 6px;
  background-color: color-mix(in srgb, var(--kg-color-warning-light) 35%, transparent);
}
.kg-context-value {
  font-size: var(--kg-fs-3xl);
  font-weight: 600;
  color: var(--kg-color-warning-dark);
  line-height: 1.1;
  white-space: nowrap;
}
.kg-context-label { font-size: var(--kg-fs-base); font-weight: 600; color: var(--kg-color-text); }
.kg-context-detail {
  font-size: var(--kg-fs-xs);
  color: var(--kg-color-text-secondary);
  line-height: 1.55;
  margin-top: 3px;
}
.kg-context-source {
  display: inline-block;
  margin-top: 5px;
  font-size: var(--kg-fs-xxs);
  color: var(--kg-color-link);
  text-decoration: none;
}
.kg-context-source:hover { text-decoration: underline; }

.kg-section-h {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 0 2px 0;
  font-size: var(--kg-fs-lg);
  font-weight: 600;
  color: var(--kg-color-text);
}
.kg-section-sub {
  font-size: var(--kg-fs-xs);
  color: var(--kg-color-text-muted);
  margin-bottom: 8px;
}

/* ─── Stat tiles (contrat « figures » de la méthode dataviz) ────────────── */

.kg-tile {
  background-color: var(--kg-color-surface);
  border: 1px solid var(--kg-color-border-light);
  border-radius: 8px;
  padding: 12px 14px;
  height: 100%;
}
.kg-tile-label {
  font-size: var(--kg-fs-xs);
  color: var(--kg-color-text-muted);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
/* Chiffres proportionnels (jamais tabular-nums sur une grande valeur). */
.kg-tile-value {
  font-family: var(--kg-font);
  font-size: var(--kg-fs-4xl);
  font-weight: 600;
  line-height: 1.1;
  color: var(--kg-color-text);
}
.kg-tile-unit { font-size: var(--kg-fs-lg); font-weight: 500; color: var(--kg-color-text-secondary); margin-left: 3px; }
.kg-tile-delta { font-size: var(--kg-fs-xs); margin-top: 5px; display: flex; align-items: center; gap: 5px; }
.kg-hero {
  font-size: 48px;
  font-weight: 600;
  line-height: 1.05;
  color: var(--kg-color-text);
  font-family: var(--kg-font);
}

/* Pastilles de statut — toujours accompagnées d'un libellé. */
.kg-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: var(--kg-fs-xxs);
  font-weight: 600;
  letter-spacing: 0.02em;
}
.kg-dot { width: 8px; height: 8px; border-radius: 9999px; flex-shrink: 0; }

/* ─── Footer (Footer.tsx) ───────────────────────────────────────────────── */

/* Ancré en bas de la fenêtre, comme le footer du MainContainer zendho :
   il reste visible quelle que soit la longueur du contenu. */
.kg-footer {
  position: fixed;
  left: var(--kg-sidebar-w);
  right: 0;
  bottom: 0;
  z-index: 110;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  padding: 8px 24px;
  border-top: 1px solid var(--kg-color-border-light);
  background-color: var(--kg-color-surface);
  color: var(--kg-color-text-muted);
  font-size: var(--kg-fs-xs);
}
.kg-org {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--kg-color-primary);
  font-size: var(--kg-fs-sm);
  font-weight: 600;
}
.kg-flag { font-size: 15px; line-height: 1; }

/* Liens du footer : la zone cliquable est portée par le conteneur, mais on
   neutralise le style de lien natif (soulignement + couleur bleue) pour
   garder l'apparence d'un simple libellé de pied de page. */
.kg-foot-lab,
.kg-foot-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  text-decoration: none !important;
  letter-spacing: 0.04em;
}
.kg-foot-lab { font-weight: 600; }
/* Icône rouge, texte noir. */
.kg-foot-lab .kg-foot-lab-icon { color: var(--kg-lab-red); display: flex; }
.kg-foot-lab .kg-foot-lab-text { color: var(--kg-color-text); }
.kg-foot-link { color: var(--kg-color-text-muted) !important; }
.kg-foot-link:hover { color: var(--kg-color-text) !important; }
.kg-foot-sep { opacity: .6; }
.kg-foot-tools { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.kg-foot-right { display: inline-flex; align-items: center; gap: 12px; }

/* ─── Widgets Streamlit realignés sur les tokens ────────────────────────── */

.stButton button {
  font-family: var(--kg-font);
  font-size: var(--kg-fs-sm);
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid var(--kg-color-border);
  background-color: var(--kg-color-surface);
  color: var(--kg-color-text-secondary);
  padding: 4px 12px;
  min-height: 30px;
  transition: 120ms ease;
}
.stButton button:hover {
  border-color: var(--kg-color-border-hover);
  background-color: var(--kg-color-surface-hover);
  color: var(--kg-color-text);
}
.stButton button[kind="primary"] {
  background-color: var(--kg-color-primary);
  border-color: var(--kg-color-primary);
  color: var(--kg-color-text-on-primary);
}
.stButton button[kind="primary"]:hover { background-color: var(--kg-color-primary-hover); }

label[data-testid="stWidgetLabel"] p {
  font-size: var(--kg-fs-xs) !important;
  font-weight: 500;
  color: var(--kg-color-text-secondary);
  margin-bottom: 2px;
}

[data-baseweb="select"] > div, [data-baseweb="input"] > div {
  font-size: var(--kg-fs-sm);
  border-radius: 6px;
  border-color: var(--kg-color-border);
  background-color: var(--kg-color-surface);
  min-height: 32px;
}
[data-baseweb="tag"] {
  background-color: var(--kg-color-primary-light) !important;
  color: var(--kg-color-primary-dark) !important;
  border-radius: 4px;
  font-size: var(--kg-fs-xs);
}

[data-testid="stDataFrame"] { border-radius: 6px; border: 1px solid var(--kg-color-border-light); }
[data-testid="stDataFrame"] * { font-size: var(--kg-fs-sm) !important; }

[data-testid="stExpander"] details {
  border: 1px solid var(--kg-color-border-light);
  border-radius: 6px;
  background-color: var(--kg-color-surface);
}
[data-testid="stExpander"] summary { font-size: var(--kg-fs-sm); font-weight: 500; }

[data-testid="stAlert"] { border-radius: 6px; font-size: var(--kg-fs-sm); padding: 10px 12px; }

/* Le graphe s'assoit dans la carte : pas de fond ni de marge parasites. */
[data-testid="stPlotlyChart"] { border-radius: 6px; overflow: hidden; }
.js-plotly-plot .plotly .modebar { opacity: .25; transition: 120ms ease; }
.js-plotly-plot .plotly:hover .modebar { opacity: 1; }

/* Focus clavier : anneau indigo fin (identique à global.css). */
:focus-visible { outline: 1px solid var(--kg-color-border-focus); outline-offset: 1px; border-radius: 4px; }
"""


def load_styles(sidebar_width=None):
    """Injecte les tokens + la feuille. À appeler une fois, au tout début du run."""

    width = sidebar_width or LAYOUT["sidebarWidth"]

    st.markdown(
        "<style>" + _vars(width) + _CSS + "</style>",
        unsafe_allow_html=True
    )


# ─── Gabarit « affiche » ─────────────────────────────────────────────────────
# Une page d'affiche n'a pas de sidebar : le menu haut porte la navigation, et
# la surface entière revient au propos. Ces règles ne sont chargées QUE par
# `socle.shell.affiche` — les charger partout ferait disparaître la sidebar du
# tableau de bord ordinaire.

_CSS_AFFICHE = """
/* La sidebar de Streamlit n'existe pas sur une affiche. `display:none` plutôt
   que `width:0` : à zéro, son bouton de repli reste cliquable et rouvre un
   panneau vide par-dessus le contenu. */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
  display: none !important;
}

/* Le conteneur principal reprend toute la largeur. Le padding par défaut de
   Streamlit (6rem en haut) creuserait un vide au-dessus du menu épinglé. */
[data-testid="stMain"] .block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ── Menu haut ─────────────────────────────────────────────────────────── */
/* Streamlit pose la classe `st-key-<cle>` sur un conteneur nommé : c'est le
   seul point d'accroche stable pour styler un VRAI bloc de widgets, qu'un
   simple <div> markdown ne pourrait pas envelopper. */

/* Le menu est une CARTE POSÉE, pas un bandeau collé au bord : la marge et le
   rayon le détachent de la page, et l'ombre lui donne le plan supérieur qu'un
   élément épinglé doit occuper quand le contenu défile dessous. */
.st-key-kgaffmenu {
  /* `width: calc(100% - 2*marge)` est indispensable : Streamlit impose
     `width:100%` aux blocs de son conteneur vertical, et une marge s'y
     AJOUTE au lieu de rétrécir l'élément — la carte débordait de 32 px et la
     bascule de langue sortait de l'écran. */
  margin: 14px auto 0;
  /* 2 × 16 px : le menu s'aligne sur le bord des CARTES du contenu. Mesuré
     avant correction, trois bords cohabitaient — boîte du menu à x=16, texte
     du menu à x=37, contenu des colonnes à x=29 — et c'est ce désaccord de 8
     à 13 px que l'œil lisait comme un défaut d'alignement sans pouvoir le
     nommer. Son rembourrage latéral vaut celui d'une carte (16 px), si bien
     que le titre du menu tombe sur le titre de la première carte. */
  width: calc(100% - 32px);
  box-sizing: border-box;
  /* Rembourrage latéral IDENTIQUE à celui d'une carte (16 px) : le titre du
     menu tombe alors exactement sur le titre de la première carte. */
  padding: 14px 16px 20px;
  background: var(--kg-color-surface);
  border: 1px solid var(--kg-color-border);
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 6px 20px rgba(15,23,42,.06);
  /* `fixed`, pas `sticky`, pour la même raison que le pied : Streamlit
     enveloppe chaque élément dans un conteneur ajusté à sa taille, où un
     élément collant n'a aucune place pour glisser — mesuré, le menu partait
     à y=-314 après 500 px de défilement. */
  position: fixed; top: 0; left: 0; right: 0; z-index: 40;
}

/* Logo et titres sur une seule ligne, alignés au centre : la silhouette est
   une marque, pas une vignette posée au-dessus du texte. */
.kg-aff-identite { display: flex; align-items: center; gap: 16px; min-width: 0; }
.kg-aff-logo {
  flex: 0 0 auto; display: flex; align-items: center;
  padding-right: 16px; border-right: 1px solid var(--kg-color-border);
}
.kg-aff-menu-id { min-width: 0; }

.kg-aff-titre {
  font-size: 25px; font-weight: 700; letter-spacing: -0.015em;
  line-height: 1.15; color: var(--kg-color-text); margin: 0;
}
.kg-aff-sous-titre {
  font-size: 13px; color: var(--kg-color-text-secondary);
  margin-top: 5px; font-variant-numeric: tabular-nums;
}
.kg-aff-surtitre {
  font-size: 10px; letter-spacing: .12em; text-transform: uppercase;
  color: var(--kg-color-primary); margin-bottom: 6px;
}

/* Le rail des boutons de vue : les boutons Streamlit sont posés dans une
   colonne, on ne fait que resserrer leur gouttière et retirer leur marge. */
/* Streamlit empile les colonnes imbriquées dès que la place manque. On force
   la rangée d'actions à rester UNE ligne, alignée à droite : le menu doit
   garder une hauteur constante quelle que soit la largeur de fenêtre. */
.st-key-kgaffactions > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"],
.st-key-kgaffactions [data-testid="stHorizontalBlock"] {
  flex-wrap: nowrap !important;
  align-items: center;
  justify-content: flex-end;
}
.st-key-kgaffactions [data-testid="stColumn"] { flex: 0 1 auto; min-width: 0; }

/* La bascule de langue ne s'étire pas : elle vaut deux fois 44 px, pas une
   fraction de la rangée. Sans cette largeur imposée, Streamlit lui donne la
   part de grille de son `st.columns` parent et elle traverse l'écran. */
.st-key-kgafflang { flex: 0 0 auto !important; width: 88px; margin-left: 10px; }
.st-key-kgafflang [data-testid="stColumn"] { flex: 1 1 46px !important; }


/* ── Boutons de vue : effet ENFONCÉ ─────────────────────────────────────
   Au repos, le bouton est légèrement soulevé (ombre portée + filet clair en
   haut). Actif ou pressé, il s'enfonce : l'ombre passe à l'INTÉRIEUR et le
   bouton descend d'un pixel. C'est le seul retour tactile qu'un écran sait
   donner, et il rend l'état actif lisible sans dépendre de la seule couleur. */
.st-key-kgaffactions [data-testid="stButton"] > button {
  font-size: 12.5px; font-weight: 560; letter-spacing: .01em;
  padding: 7px 14px; min-height: 36px; white-space: nowrap;
  border: 1px solid var(--kg-color-border);
  transition: box-shadow .12s ease, transform .08s ease, background .12s ease;
  border-radius: 9px;
  background: var(--kg-color-surface);
  color: var(--kg-color-text-secondary);
  box-shadow: 0 1px 0 rgba(255,255,255,.7) inset, 0 1px 2px rgba(15,23,42,.07);
}
.st-key-kgaffactions [data-testid="stButton"] > button:hover {
  background: var(--kg-color-surface-hover);
  color: var(--kg-color-text);
  border-color: var(--kg-color-border-hover);
}
/* Pression réelle du doigt ou de la souris. */
.st-key-kgaffactions [data-testid="stButton"] > button:active {
  transform: translateY(1px);
  box-shadow: inset 0 2px 5px rgba(15,23,42,.16);
}
/* État ACTIF — le bouton reste enfoncé tant que la vue est la sienne. */
.st-key-kgaffactions [data-testid="stButton"] > button[kind="primary"] {
  background: var(--kg-color-primary);
  color: var(--kg-color-text-on-primary);
  border-color: var(--kg-color-primary-dark);
  transform: translateY(1px);
  box-shadow: inset 0 2px 6px rgba(0,0,0,.28), inset 0 -1px 0 rgba(255,255,255,.12);
}
.st-key-kgaffactions [data-testid="stButton"] > button[kind="primary"]:hover {
  background: var(--kg-color-primary-hover);
  color: var(--kg-color-text-on-primary);
}

/* ── Bascule de langue : un seul objet, deux moitiés ────────────────────
   Les deux boutons sont SOUDÉS — gouttière annulée, rayons portés par les
   extrémités du groupe. Une bascule se lit comme un interrupteur, pas comme
   deux boutons indépendants qui se trouveraient côte à côte. */
.st-key-kgafflang [data-testid="stHorizontalBlock"] { gap: 0 !important; }
.st-key-kgafflang [data-testid="stColumn"] { min-width: 0; }

.st-key-kgafflang [data-testid="stButton"] > button {
  border-radius: 0; padding: 7px 6px; font-weight: 650; font-size: 11.5px;
  letter-spacing: .06em;
  background: var(--kg-color-surface-secondary);
  color: var(--kg-color-text-muted);
  box-shadow: inset 0 1px 3px rgba(15,23,42,.07);
}
.st-key-kgafflang [data-testid="stColumn"]:first-child button {
  border-radius: 9px 0 0 9px;
}
.st-key-kgafflang [data-testid="stColumn"]:last-child button {
  border-radius: 0 9px 9px 0; border-left-width: 0;
}
.st-key-kgafflang [data-testid="stButton"] > button:hover {
  color: var(--kg-color-text); background: var(--kg-color-surface-hover);
}
/* La langue active REMONTE : c'est la moitié en relief qui est choisie,
   l'autre reste en creux. L'inverse des vues, et c'est voulu — une bascule
   montre où l'on est, un onglet montre ce qu'on a enfoncé. */
.st-key-kgafflang [data-testid="stButton"] > button[kind="primary"] {
  background: var(--kg-color-surface);
  color: var(--kg-color-primary);
  border-color: var(--kg-color-primary);
  box-shadow: 0 1px 3px rgba(15,23,42,.12);
  position: relative; z-index: 1;
}

/* ── Corps en deux colonnes ────────────────────────────────────────────── */
/* Le haut réserve la place du menu, qui est en `fixed` et ne pousse donc plus
   rien : hauteur de la carte (variable, posée par la prop `hauteur_menu`)
   plus sa marge haute et l'écart de respiration.
   Écrit en RACCOURCI et non en `padding-top` séparé : un raccourci déclaré
   plus loin dans la feuille écraserait la propriété isolée — c'est ce qui
   est arrivé, et les colonnes passaient 98 px sous le header. */
/* 15 px de côté, et non 16 : les colonnes portent elles-mêmes 12 px de
   rembourrage plus 1 px de filet, si bien que la CARTE se pose à 15 + 13 =
   28 px du bord — exactement la gouttière définie plus bas. Une marge de page
   et une gouttière inégales (mesurées à 29 et 38 px) sont précisément ce qui
   donne l'impression de séparations arbitraires. */
/* UNE SEULE valeur de séparation sur toute la page — 16 px — entre le menu et
   la première carte, entre deux cartes, entre les deux colonnes, et du bord de
   la fenêtre. La réserve haute s'écrit comme la somme qu'elle est vraiment :

       14 (marge haute du menu) + hauteur_menu + 16 (écart)
       − 24 (rembourrage propre au conteneur principal de Streamlit)
       − 1  (filet de la colonne, qui compte lui aussi)
     = hauteur_menu + 5

   Le « + 26 px » d'origine ignorait ces 24 px et les 12 px que portait alors
   la colonne : le vide sous le menu atteignait 49 px. Les 15 px de côté
   suivent la même règle — 15 + 1 de filet = 16. */
.st-key-kgaffcorps { padding: calc(var(--kg-aff-menu-h, 116px) + 5px) 15px 8px; }

/* L'écart vertical est une VARIABLE : le bandeau d'onglets doit pouvoir le
   reprendre au pixel pour venir se coller à sa carte. */
.st-key-kgaffcorps { --kg-aff-ecart: 16px; }

/* Gouttière : les colonnes ne portent plus de rembourrage, l'écart entre les
   cartes EST donc ce `gap` — 16 px, comme partout ailleurs.
   `:has()` cible la SEULE rangée qui porte la colonne de gauche. Écrite sans
   ce filtre, la règle s'appliquait à TOUS les blocs horizontaux du corps :
   les quatre tuiles se retrouvaient collées à 2 px les unes des autres, et
   les deux champs de la zone de filtres aussi. Une règle de mise en page qui
   ne dit pas à QUOI elle s'applique finit toujours par s'appliquer à tout. */
[data-testid="stHorizontalBlock"]:has(> div [class*="st-key-kgaffgauche"]) {
  /* 14 et non 16 : les deux colonnes portent chacune un filet d'un pixel, qui
     s'ajoute de part et d'autre de la gouttière. */
  gap: 14px;
}

/* Rythme vertical UNIQUE. Avant : 10 px d'écart de bloc AUXQUELS s'ajoutait
   la `margin-top: 8px` que toute carte porte — soit 18 px entre deux cartes,
   mais 10 px seulement sous la zone de filtres, qui n'est pas une carte. Deux
   espacements pour la même intention, et l'œil voyait le désaccord sans
   pouvoir le nommer. La marge est neutralisée, l'écart devient la seule règle. */
.st-key-kgaffcorps [data-testid="stVerticalBlock"] { gap: var(--kg-aff-ecart); }
.st-key-kgaffcorps [class*="st-key-kgcard"] { margin-top: 0; }

/* La colonne de droite se comporte comme un panneau : fond légèrement en
   retrait, pour que la carte s'y détache sans cadre dessiné. */
/* Les colonnes n'ont AUCUN décor par défaut : fond, bordure et filet sont
   décidés par `render_affiche` (props `separation_colonnes`, `colonne_*`) et
   injectés en surcouche. Une règle ici ferait double emploi et gagnerait
   parfois, selon l'ordre d'injection. */

/* Le pied est ÉPINGLÉ en bas, comme le menu l'est en haut : sur une affiche
   dont les colonnes dépassent la hauteur de fenêtre, un pied en fin de flux
   n'est jamais vu. La source et l'auteur doivent rester lisibles sans avoir
   à faire défiler jusqu'au bout. */
/* `fixed` et non `sticky` : Streamlit enveloppe CHAQUE élément dans un
   conteneur ajusté à sa taille, si bien qu'un élément collant n'a aucune
   place pour glisser dans son parent — il reste en fin de flux et ne colle
   jamais. Seul `fixed`, qui sort du flux et se cale sur la fenêtre, tient. */
.kg-aff-pied {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 30;
  display: flex; justify-content: space-between; align-items: center;
  /* Un pied ne porte qu'une source et une signature : il doit se faire
     oublier. 6 px suffisent — au-delà, il prend la place d'un contenu. */
  gap: 16px; padding: 6px 30px; line-height: 1.5;
  border-top: 1px solid var(--kg-color-border);
  /* Fond opaque obligatoire : le contenu défile SOUS le pied, et sans lui
     les textes se superposeraient. */
  background: var(--kg-color-background);
  font-size: 11.5px; color: var(--kg-color-text-muted);
}

/* Le pied étant hors du flux, il recouvrirait la fin du contenu : on rend
   sa hauteur au corps sous forme de marge basse. */
.st-key-kgaffcorps { padding-bottom: 40px !important; }

/* Sous 1 100 px, les deux colonnes ne tiennent plus côte à côte : Streamlit
   les empile de lui-même, mais le panneau garderait sa hauteur de carte. */
@media (max-width: 1100px) {
  .st-key-kgaffmenu { position: static; margin: 10px auto 0;
                      width: calc(100% - 20px);
                      padding: 14px 16px 12px; }
  .st-key-kgaffactions { justify-content: flex-start; }
  .st-key-kgaffcorps { padding: calc(var(--kg-aff-menu-h, 116px) + 20px) 10px 8px; }
}
"""


def load_styles_affiche():
    """Feuille du tableau de bord + surcouche « affiche ».

    Appelée à la place de `load_styles`, jamais en plus : les deux injectent
    les mêmes variables, et un double chargement doublerait la feuille dans
    le document à chaque rerun.
    """

    st.markdown(
        "<style>" + _vars(0) + _CSS + _CSS_AFFICHE + "</style>",
        unsafe_allow_html=True,
    )
