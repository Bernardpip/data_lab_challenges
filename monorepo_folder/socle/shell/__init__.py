"""La coquille « admin » : sidebar → topbar → onglets → contenu → footer.

Un défi n'appelle qu'une chose :

    from socle.shell import render_shell
    render_shell(brand=BRAND, content_registry=CONTENT_REGISTRY,
                 sections=NAV_SECTIONS)

Règles dures portées ici, et qu'il ne faut pas défaire :

  · navigation par `st.button` — une ancre rechargerait le document ;
  · `reset_cards()` à chaque run ;
  · le scroll-top consommé UNE seule fois après `go()` ;
  · la largeur de sidebar connue AVANT de peindre la feuille de style.
"""

from socle.shell.app_shell import render_shell
from socle.shell.affiche import render_affiche
from socle.shell.nav import find_section, find_item, verifier_nav

__all__ = ["render_shell", "render_affiche", "find_section", "find_item", "verifier_nav"]
