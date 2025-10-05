#!/bin/bash

# Script de lancement optimisé pour TikTok to YouTube Desktop
# Version finale avec gestion automatique de l'environnement

echo "🚀 Démarrage de TikTok to YouTube Converter..."
echo "================================================"

# Vérification du répertoire de travail
if [ ! -f "main_optimized.py" ]; then
    echo "❌ Erreur: Veuillez exécuter ce script depuis le dossier desktop_app"
    exit 1
fi

# Détection du système d'exploitation
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
    PYTHON_CMD="python3"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
    PYTHON_CMD="python3"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="Windows"
    PYTHON_CMD="python"
else
    PLATFORM="Inconnu"
    PYTHON_CMD="python3"
fi

echo "🖥️  Plateforme détectée: $PLATFORM"

# Fonction de vérification de Python
check_python() {
    if command -v $PYTHON_CMD &> /dev/null; then
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
        echo "🐍 Python trouvé: $PYTHON_VERSION"
        return 0
    else
        echo "❌ Python non trouvé. Veuillez installer Python 3.9+"
        return 1
    fi
}

# Fonction de création d'environnement virtuel
setup_venv() {
    if [ ! -d ".venv-desktop" ]; then
        echo "📦 Création de l'environnement virtuel..."
        $PYTHON_CMD -m venv .venv-desktop
        if [ $? -ne 0 ]; then
            echo "❌ Erreur lors de la création de l'environnement virtuel"
            exit 1
        fi
    fi
    
    # Activation de l'environnement virtuel
    if [[ "$PLATFORM" == "Windows" ]]; then
        source .venv-desktop/Scripts/activate
    else
        source .venv-desktop/bin/activate
    fi
    
    echo "✅ Environnement virtuel activé"
}

# Fonction d'installation des dépendances
install_dependencies() {
    echo "📚 Vérification des dépendances..."
    
    # Installation de PyQt6
    if ! python -c "import PyQt6" 2>/dev/null; then
        echo "📦 Installation de PyQt6..."
        pip install PyQt6>=6.6.0
    fi
    
    # Installation des autres dépendances si disponibles
    if [ -f "requirements.txt" ]; then
        echo "📦 Installation des dépendances supplémentaires..."
        pip install -r requirements.txt
    fi
    
    echo "✅ Dépendances installées"
}

# Fonction de lancement de l'application
launch_app() {
    echo "🎬 Lancement de l'application..."
    echo ""
    
    # Priorité à la version optimisée
    if [ -f "main_optimized.py" ]; then
        python main_optimized.py
    elif [ -f "main.py" ]; then
        python main.py
    else
        echo "❌ Aucun fichier principal trouvé"
        exit 1
    fi
}

# Fonction de nettoyage
cleanup() {
    echo ""
    echo "🧹 Nettoyage en cours..."
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate 2>/dev/null || true
    fi
    echo "👋 Merci d'avoir utilisé TikTok to YouTube Converter!"
}

# Piège pour nettoyer en cas d'interruption
trap cleanup EXIT

# Exécution principale
main() {
    # Vérifications préliminaires
    if ! check_python; then
        exit 1
    fi
    
    # Configuration de l'environnement
    setup_venv
    install_dependencies
    
    echo ""
    echo "🎉 Tout est prêt!"
    echo "▶️  Démarrage de l'application..."
    echo ""
    
    # Lancement
    launch_app
}

# Point d'entrée
main "$@"