#!/usr/bin/env bash
#
# Démarrage du tableau de bord — macOS et Linux.
#
# Enchaîne trois choses, et s'arrête à la première qui bloque :
#   1. trouver un interpréteur Python utilisable ;
#   2. lancer le diagnostic (verifier.py) ;
#   3. lancer Streamlit, seulement si le diagnostic est vert.
#
# Le script n'installe rien de lui-même : il propose, et attend une réponse.
# Un utilisateur qui décompresse une archive ne s'attend pas à ce qu'un script
# modifie son système sans le lui demander.

set -u

cd "$(dirname "$0")" || exit 1

gras=""; normal=""; rouge=""; vert=""
if [ -t 1 ]; then
    gras="\033[1m"; normal="\033[0m"; rouge="\033[31m"; vert="\033[32m"
fi

printf "\n${gras}  Adéquation formation-emploi au Togo${normal}\n"
printf "  Data Challenge Éducation · Défi 2\n\n"

# ─── 1. Trouver Python ───────────────────────────────────────────────────────
# Un environnement virtuel déjà présent dans le dossier prime : c'est là que
# les bibliothèques du projet ont le plus de chances d'être installées.

PYTHON=""

if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    printf "  Environnement virtuel du projet détecté (.venv)\n"
else
    for candidat in python3 python; do
        if command -v "$candidat" >/dev/null 2>&1; then
            # `python` peut encore désigner Python 2 sur d'anciens systèmes.
            if "$candidat" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 9) else 1)' 2>/dev/null; then
                PYTHON="$candidat"
                break
            fi
        fi
    done
fi

if [ -z "$PYTHON" ]; then
    printf "${rouge}  Python 3.9 ou plus récent est introuvable sur cette machine.${normal}\n\n"
    printf "  À faire :\n"
    case "$(uname -s)" in
        Darwin) printf "    • installer depuis https://www.python.org/downloads/\n"
                printf "    • ou, avec Homebrew :  brew install python\n" ;;
        Linux)  printf "    • Debian / Ubuntu :  sudo apt install python3 python3-venv python3-pip\n"
                printf "    • Fedora :           sudo dnf install python3 python3-pip\n" ;;
        *)      printf "    • installer depuis https://www.python.org/downloads/\n" ;;
    esac
    printf "\n  Puis relancez :  ./demarrer.sh\n\n"
    exit 1
fi

printf "  Python utilisé : %s (%s)\n" "$("$PYTHON" -V 2>&1)" "$PYTHON"

# ─── 2. Diagnostic ───────────────────────────────────────────────────────────

"$PYTHON" verifier.py
diagnostic=$?

if [ $diagnostic -ne 0 ]; then
    printf "\n"
    printf "  Le diagnostic signale des manques. Voulez-vous installer les\n"
    printf "  bibliothèques maintenant ? Cela lancera :\n\n"
    printf "    %s -m pip install -r requirements.txt\n\n" "$PYTHON"
    printf "  Installer ? [o/N] "
    read -r reponse

    case "$reponse" in
        [oOyY]*)
            printf "\n"
            "$PYTHON" -m pip install -r requirements.txt || {
                printf "\n${rouge}  L'installation a échoué.${normal}\n"
                printf "  Essayez dans un environnement virtuel :\n"
                printf "    %s -m venv .venv && source .venv/bin/activate\n" "$PYTHON"
                printf "    pip install -r requirements.txt\n\n"
                exit 1
            }
            printf "\n  Nouveau diagnostic :\n"
            "$PYTHON" verifier.py || exit 1
            ;;
        *)
            printf "\n  Rien n'a été installé. Relancez ./demarrer.sh quand vous\n"
            printf "  serez prêt, ou suivez les commandes affichées ci-dessus.\n\n"
            exit 1
            ;;
    esac
fi

# ─── 3. Lancement ────────────────────────────────────────────────────────────

printf "\n${vert}  Lancement du tableau de bord…${normal}\n"
printf "  Une fois le navigateur ouvert : ${gras}zoom 75 %%${normal}, largeur ≥ 1 440 px.\n"
printf "  Pour arrêter : Ctrl+C dans ce terminal.\n\n"

exec "$PYTHON" -m streamlit run app.py
