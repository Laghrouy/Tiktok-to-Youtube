#!/bin/bash

# Script de lancement pour l'application TikTok to YouTube Desktop

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 TikTok to YouTube Desktop Application${NC}"
echo -e "${BLUE}======================================${NC}"

# Vérifier si nous sommes dans le bon répertoire
if [ ! -f "desktop_app/main.py" ]; then
    echo -e "${RED}❌ Erreur: Veuillez exécuter ce script depuis le répertoire racine du projet${NC}"
    exit 1
fi

# Vérifier si l'environnement virtuel existe
if [ ! -d ".venv-desktop" ]; then
    echo -e "${YELLOW}⚠️  Environnement virtuel non trouvé. Création en cours...${NC}"
    python3 -m venv .venv-desktop
    
    echo -e "${BLUE}📦 Installation des dépendances...${NC}"
    source .venv-desktop/bin/activate
    pip install PyQt6 -r requirements.txt
fi

# Activer l'environnement virtuel
echo -e "${GREEN}🔧 Activation de l'environnement virtuel...${NC}"
source .venv-desktop/bin/activate

# Vérifier les dépendances
echo -e "${BLUE}🔍 Vérification des dépendances...${NC}"
python -c "import PyQt6; print('✅ PyQt6 installé')" || {
    echo -e "${RED}❌ PyQt6 non installé. Installation...${NC}"
    pip install PyQt6
}

# Lancer l'application
echo -e "${GREEN}🎬 Lancement de l'application...${NC}"
echo ""

# Choisir quelle version lancer
echo "Quelle version voulez-vous lancer ?"
echo "1) Version complète (avec toutes les fonctionnalités)"
echo "2) Version démonstration (interface uniquement)"
echo ""
read -p "Votre choix (1 ou 2): " choice

case $choice in
    1)
        echo -e "${GREEN}🚀 Lancement de la version complète...${NC}"
        python desktop_app/main.py
        ;;
    2)
        echo -e "${GREEN}🎨 Lancement de la version démonstration...${NC}"
        python desktop_app/demo.py
        ;;
    *)
        echo -e "${YELLOW}Choix invalide. Lancement de la version démonstration par défaut...${NC}"
        python desktop_app/demo.py
        ;;
esac

echo -e "${BLUE}👋 Merci d'avoir utilisé TikTok to YouTube Desktop!${NC}"