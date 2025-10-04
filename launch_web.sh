#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

## Charger un fichier .env local si présent (variables exportées)
if [ -f .env ]; then
    # Exporter automatiquement toutes les variables définies dans .env
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

## Build Tailwind CSS if possible (non-fatal)
if command -v npm >/dev/null 2>&1; then
    if [ -f package.json ]; then
        echo "[launch] Building Tailwind CSS (npm run tailwind:build)…" || true
        if npm run --silent tailwind:build >/dev/null 2>&1; then
            echo "[launch] Tailwind CSS built." || true
        else
            echo "[launch] Tailwind build failed, continuing with fallback CSS." || true
        fi
    fi
fi

# Activer venv si présent
if [ -d .venv-desktop ]; then
    if [ -f .venv-desktop/bin/activate ]; then
        # shellcheck disable=SC1091
        source .venv-desktop/bin/activate
    else
        echo "[launcher] Avertissement: .venv-desktop existe mais aucun activateur trouvé; on continue avec l'interpréteur système."
    fi
fi

# Choisir l'interpréteur Python disponible
if command -v python >/dev/null 2>&1; then
    PYBIN=$(command -v python)
elif command -v python3 >/dev/null 2>&1; then
    PYBIN=$(command -v python3)
else
    echo "[launcher] Erreur: Python introuvable (ni 'python' ni 'python3')." >&2
    exit 127
fi

# Lancer le serveur FastAPI + fenêtre pywebview
"$PYBIN" - <<'PY'
import threading, time, sys
import webbrowser
import socket

def find_free_port(pref=8765):
    # essaie pref puis 8766..8775
    ports = [pref] + list(range(8766, 8776))
    for p in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p))
            except OSError:
                continue
            return p
    return pref

# Démarre uvicorn en thread
def run_server(port):
    import uvicorn
    uvicorn.run("webapp.app:app", host="127.0.0.1", port=port, reload=False, log_level="info")

PORT = find_free_port(8765)
th = threading.Thread(target=run_server, args=(PORT,), daemon=True)
th.start()

# Attendre que le serveur soit prêt
import socket
for _ in range(50):
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
            break
    except Exception:
        time.sleep(0.1)

def open_url_smart(url: str):
    import os, subprocess, platform, shutil
    # Respecter T2Y_NO_BROWSER
    if os.environ.get('T2Y_NO_BROWSER'):
        print(f"T2Y_NO_BROWSER=1 — ouvrez manuellement: {url}")
        return False
    # Détection WSL
    is_wsl = 'microsoft' in platform.release().lower() or os.environ.get('WSL_DISTRO_NAME')
    try:
        if is_wsl:
            if shutil.which('wslview'):
                subprocess.run(['wslview', url], check=False)
                return True
            # Fallback vers powershell si disponible
            if shutil.which('powershell.exe'):
                subprocess.run(['powershell.exe', '-NoProfile', 'Start-Process', url], check=False)
                return True
        if sys.platform.startswith('linux'):
            if shutil.which('xdg-open'):
                subprocess.run(['xdg-open', url], check=False)
                return True
        if sys.platform == 'darwin':
            subprocess.run(['open', url], check=False)
            return True
        if sys.platform.startswith('win'):
            try:
                os.startfile(url)  # type: ignore[attr-defined]
                return True
            except Exception:
                subprocess.run(['cmd', '/c', 'start', '', url], shell=True, check=False)
                return True
    except Exception:
        pass
    # Dernier recours: webbrowser
    try:
        webbrowser.open_new_tab(url)
        return True
    except Exception:
        print(f"Impossible d'ouvrir automatiquement le navigateur. URL: {url}")
        return False

# Essayer pywebview, sinon ouvrir le navigateur (avec fallbacks WSL/x86)
url = f'http://127.0.0.1:{PORT}/'
print(f"[launcher] serveur prévu sur: {url}")
try:
    import webview
    webview.create_window('TikTok → YouTube', url)
    webview.start()
except Exception as e:
    print('[launcher] pywebview indisponible:', e)
    print('[launcher] ouverture du navigateur:', url)
    open_url_smart(url)
    # Garder le process vivant
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
PY
