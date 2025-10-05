#!/bin/bash

# Script de lancement pour l'interface Tkinter (ttkbootstrap)
# Aligne le comportement avec launch_desktop.sh / desktop_app/launch_optimized.sh

set -euo pipefail

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 TikTok → YouTube (Tkinter)${NC}"
echo -e "${BLUE}================================${NC}"

# Vérifier répertoire racine
if [ ! -f "tiktok_to_youtube.py" ]; then
  echo -e "${RED}❌ Erreur: exécutez ce script depuis la racine du projet${NC}"
  exit 1
fi

# Détection plate-forme + binaire python
if [[ "${OSTYPE:-linux-gnu}" == linux-* ]]; then
  PY=python3
elif [[ "${OSTYPE:-}" == darwin* ]]; then
  PY=python3
else
  PY=python3
fi

# Créer venv si manquant
if [ ! -d ".venv-desktop" ]; then
  echo -e "${YELLOW}⚠️  Environnement virtuel manquant → création…${NC}"
  $PY -m venv .venv-desktop
fi

# Activer venv
source .venv-desktop/bin/activate

# Environnements headless: forcer l'OAuth console si pas de display
if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
  export T2Y_NO_BROWSER=1
fi

# Installer dépendances
echo -e "${BLUE}🔍 Vérification des dépendances…${NC}"
python - <<'PY'
import importlib, sys
missing = []
for m in ("ttkbootstrap", "PIL", "yt_dlp", "googleapiclient", "google_auth_oauthlib"):
    try:
        importlib.import_module(m)
    except Exception:
        missing.append(m)
if missing:
    print("MISSING:" + ",".join(missing))
else:
    print("OK")
PY

NEED=$(python - <<'PY'
import importlib, sys
mods = ["ttkbootstrap", "PIL", "yt_dlp", "googleapiclient", "google_auth_oauthlib"]
missing = []
for m in mods:
    try:
        importlib.import_module(m)
    except Exception:
        missing.append(m)
print(' '.join(missing))
PY
)

if [ -n "${NEED}" ]; then
  echo -e "${YELLOW}📦 Installation des dépendances manquantes… (${NEED})${NC}"
  pip install -r requirements.txt
fi

# Lancer application Tkinter
echo -e "${GREEN}🎬 Lancement de l'interface Tkinter…${NC}\n"
exec python tiktok_to_youtube.py "$@"
