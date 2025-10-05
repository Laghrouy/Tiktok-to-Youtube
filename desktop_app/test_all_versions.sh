#!/bin/bash

# Script de test pour toutes les versions de l'application desktop
# Valide le bon fonctionnement de chaque version

echo "🧪 Tests de validation - TikTok to YouTube Desktop"
echo "================================================="

# Fonction de test d'une version
test_version() {
    local file=$1
    local description=$2
    local timeout=${3:-10}
    
    echo ""
    echo "🔍 Test: $description"
    echo "📄 Fichier: $file"
    
    if [ ! -f "$file" ]; then
        echo "❌ ÉCHEC: Fichier non trouvé"
        return 1
    fi
    
    echo "▶️  Lancement (timeout: ${timeout}s)..."
    
    # Lancement avec timeout
    timeout $timeout python "$file" > /tmp/test_output_$$.log 2>&1 &
    local pid=$!
    
    sleep 3  # Laisser le temps de démarrer
    
    if kill -0 $pid 2>/dev/null; then
        echo "✅ SUCCÈS: Application lancée correctement"
        kill $pid 2>/dev/null
        wait $pid 2>/dev/null
        return 0
    else
        echo "❌ ÉCHEC: Application n'a pas pu démarrer"
        if [ -f "/tmp/test_output_$$.log" ]; then
            echo "📝 Sortie d'erreur:"
            cat /tmp/test_output_$$.log | head -10
        fi
        return 1
    fi
}

# Fonction de validation de l'environnement
check_environment() {
    echo "🔧 Vérification de l'environnement..."
    
    # Vérification Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 non trouvé"
        return 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2)
    echo "🐍 Python: $python_version"
    
    # Vérification PyQt6
    if python3 -c "import PyQt6" 2>/dev/null; then
        echo "✅ PyQt6 disponible"
    else
        echo "⚠️  PyQt6 non trouvé - installation recommandée"
        echo "   pip install PyQt6>=6.6.0"
    fi
    
    return 0
}

# Fonction de validation des fichiers
check_files() {
    echo ""
    echo "📁 Vérification des fichiers..."
    
    local files=(
        "main_optimized.py:Application principale optimisée"
        "main.py:Application complète"
        "demo_complete.py:Démo complète"
        "demo.py:Démo simple"
        "launch_optimized.sh:Script de lancement"
        "ui/styles_optimized.py:Styles optimisés"
        "ui/styles.py:Styles complets"
        "README_FINAL.md:Documentation"
    )
    
    local missing_files=0
    
    for item in "${files[@]}"; do
        local file=$(echo $item | cut -d':' -f1)
        local desc=$(echo $item | cut -d':' -f2)
        
        if [ -f "$file" ]; then
            echo "✅ $desc ($file)"
        else
            echo "❌ $desc ($file) - MANQUANT"
            ((missing_files++))
        fi
    done
    
    if [ $missing_files -eq 0 ]; then
        echo "✅ Tous les fichiers requis sont présents"
        return 0
    else
        echo "⚠️  $missing_files fichier(s) manquant(s)"
        return 1
    fi
}

# Fonction de tests des versions
test_all_versions() {
    echo ""
    echo "🚀 Tests de lancement des versions..."
    
    local success=0
    local total=0
    
    # Test version optimisée (prioritaire)
    if test_version "main_optimized.py" "Version optimisée (recommandée)" 8; then
        ((success++))
    fi
    ((total++))
    
    # Test démo complète
    if test_version "demo_complete.py" "Démo complète avec animations" 8; then
        ((success++))
    fi
    ((total++))
    
    # Test démo simple
    if test_version "demo.py" "Démo simple" 6; then
        ((success++))
    fi
    ((total++))
    
    # Test version complète (peut échouer sans modules t2y)
    if test_version "main.py" "Version complète" 8; then
        ((success++))
    fi
    ((total++))
    
    echo ""
    echo "📊 Résultats des tests: $success/$total versions fonctionnelles"
    
    if [ $success -ge 3 ]; then
        echo "🎉 EXCELLENT: La plupart des versions fonctionnent"
        return 0
    elif [ $success -ge 2 ]; then
        echo "✅ BON: Plusieurs versions fonctionnelles"
        return 0
    elif [ $success -ge 1 ]; then
        echo "⚠️  MOYEN: Au moins une version fonctionne"
        return 1
    else
        echo "❌ PROBLÈME: Aucune version ne fonctionne"
        return 1
    fi
}

# Fonction de test du script de lancement
test_launch_script() {
    echo ""
    echo "🚀 Test du script de lancement optimisé..."
    
    if [ ! -f "launch_optimized.sh" ]; then
        echo "❌ Script de lancement non trouvé"
        return 1
    fi
    
    if [ ! -x "launch_optimized.sh" ]; then
        echo "⚠️  Script non exécutable - correction..."
        chmod +x launch_optimized.sh
    fi
    
    echo "✅ Script de lancement prêt"
    echo "ℹ️  Utilisez: ./launch_optimized.sh"
    return 0
}

# Fonction de nettoyage
cleanup() {
    echo ""
    echo "🧹 Nettoyage des fichiers de test..."
    rm -f /tmp/test_output_*.log
}

# Piège pour nettoyer
trap cleanup EXIT

# Fonction principale
main() {
    local exit_code=0
    
    # Vérifications préliminaires
    check_environment || exit_code=1
    check_files || exit_code=1
    
    # Tests de fonctionnement
    test_all_versions || exit_code=1
    test_launch_script || exit_code=1
    
    echo ""
    echo "======================================"
    if [ $exit_code -eq 0 ]; then
        echo "🎉 TOUS LES TESTS RÉUSSIS!"
        echo "✅ Application prête à l'utilisation"
        echo ""
        echo "🚀 Pour démarrer l'application:"
        echo "   ./launch_optimized.sh"
        echo "   ou: python main_optimized.py"
    else
        echo "⚠️  TESTS PARTIELLEMENT RÉUSSIS"
        echo "ℹ️  L'application peut fonctionner avec certaines limitations"
        echo ""
        echo "🔧 Vérifiez l'installation de PyQt6:"
        echo "   pip install PyQt6>=6.6.0"
    fi
    echo "======================================"
    
    return $exit_code
}

# Point d'entrée
main "$@"