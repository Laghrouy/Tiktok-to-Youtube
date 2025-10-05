#!/bin/bash

# Script pour créer un exécutable standalone de l'application

echo "🔨 Création d'un exécutable standalone pour TikTok to YouTube Desktop"
echo "=================================================================="

# Vérifier si PyInstaller est installé
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installation de PyInstaller..."
    source .venv-desktop/bin/activate
    pip install pyinstaller
fi

# Activer l'environnement virtuel
source .venv-desktop/bin/activate

# Créer le répertoire de build s'il n'existe pas
mkdir -p build_desktop

echo "🚀 Création de l'exécutable..."

# Créer l'exécutable avec PyInstaller
pyinstaller --onefile \
    --windowed \
    --name "TikTok-to-YouTube-Desktop" \
    --icon=desktop_app/assets/icon.ico \
    --add-data "t2y:t2y" \
    --add-data "desktop_app/ui:desktop_app/ui" \
    --distpath build_desktop/dist \
    --workpath build_desktop/work \
    --specpath build_desktop \
    desktop_app/main.py

# Vérifier si la création a réussi
if [ -f "build_desktop/dist/TikTok-to-YouTube-Desktop" ]; then
    echo "✅ Exécutable créé avec succès !"
    echo "📍 Emplacement : build_desktop/dist/TikTok-to-YouTube-Desktop"
    
    # Créer un package avec les fichiers nécessaires
    echo "📦 Création du package de distribution..."
    mkdir -p build_desktop/package
    cp build_desktop/dist/TikTok-to-YouTube-Desktop build_desktop/package/
    cp README.md build_desktop/package/
    cp desktop_app/README.md build_desktop/package/README-Desktop.md
    cp client_secret.json build_desktop/package/ 2>/dev/null || echo "⚠️  client_secret.json non trouvé - à ajouter manuellement"
    
    # Créer un script de lancement
    cat > build_desktop/package/launch.sh << 'EOF'
#!/bin/bash
echo "🚀 Lancement de TikTok to YouTube Desktop..."
./TikTok-to-YouTube-Desktop
EOF
    chmod +x build_desktop/package/launch.sh
    
    # Créer une archive
    cd build_desktop
    tar -czf TikTok-to-YouTube-Desktop-Linux.tar.gz package/
    cd ..
    
    echo "📦 Package créé : build_desktop/TikTok-to-YouTube-Desktop-Linux.tar.gz"
    echo ""
    echo "🎉 Build terminé avec succès !"
    echo ""
    echo "Pour distribuer l'application :"
    echo "1. Partagez le fichier .tar.gz"
    echo "2. L'utilisateur doit extraire l'archive"
    echo "3. Exécuter ./launch.sh ou directement ./TikTok-to-YouTube-Desktop"
    echo ""
    echo "⚠️  N'oubliez pas d'inclure client_secret.json pour l'authentification YouTube"
    
else
    echo "❌ Erreur lors de la création de l'exécutable"
    exit 1
fi