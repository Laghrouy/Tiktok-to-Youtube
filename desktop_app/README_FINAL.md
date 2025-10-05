# 🎬 TikTok to YouTube Desktop - Guide Complet

## 📋 Présentation

TikTok to YouTube Desktop est une application moderne avec interface graphique PyQt6 qui permet de convertir facilement vos vidéos TikTok en contenu YouTube optimisé.

### ✨ Caractéristiques principales

- **Interface moderne** : Design sombre avec effets de glassmorphism
- **Traitement automatisé** : Téléchargement, traitement et upload automatiques
- **Métadonnées intelligentes** : Génération automatique des titres, descriptions et tags
- **Multi-plateforme** : Compatible Linux, macOS et Windows
- **Configuration avancée** : Options de qualité, watermarks, et personnalisation

## 🚀 Installation et Démarrage

### Méthode recommandée (Script automatique)

```bash
cd desktop_app
./launch_optimized.sh
```

Le script gère automatiquement :
- ✅ Détection de Python et de la plateforme
- ✅ Création de l'environnement virtuel
- ✅ Installation des dépendances
- ✅ Lancement de l'application

### Installation manuelle

1. **Créer l'environnement virtuel**
```bash
python3 -m venv .venv-desktop
source .venv-desktop/bin/activate  # Linux/macOS
# ou
.venv-desktop\Scripts\activate     # Windows
```

2. **Installer les dépendances**
```bash
pip install PyQt6>=6.6.0
pip install -r requirements.txt  # optionnel
```

3. **Lancer l'application**
```bash
python main_optimized.py
```

## 📁 Structure du Projet

```
desktop_app/
├── main_optimized.py          # Application principale optimisée
├── main.py                    # Version complète avec intégration t2y
├── demo_complete.py           # Démo complète avec animations
├── demo.py                    # Démo simple
├── launch_optimized.sh        # Script de lancement automatique
├── config.py                  # Configuration de l'application
├── requirements.txt           # Dépendances Python
└── ui/                        # Module interface utilisateur
    ├── styles_optimized.py    # Styles CSS optimisés pour PyQt6
    ├── styles.py              # Styles complets
    ├── main_window.py         # Fenêtre principale
    ├── components.py          # Composants UI personnalisés
    ├── preferences.py         # Fenêtre de préférences
    └── about.py               # Fenêtre À propos
```

## 🎨 Versions Disponibles

### 1. Version Optimisée (`main_optimized.py`)
- ✅ **Recommandée pour l'utilisation quotidienne**
- ✅ Styles CSS optimisés sans avertissements
- ✅ Interface complète avec onglets
- ✅ Compatible mode démo et production

### 2. Version Complète (`main.py`)
- ✅ Intégration complète avec les modules t2y
- ⚠️ Peut afficher des avertissements CSS cosmétiques
- ✅ Fonctionnalités avancées de traitement

### 3. Démo Complète (`demo_complete.py`)
- ✅ Démonstration de toutes les fonctionnalités UI
- ✅ Animations et effets visuels
- ✅ Indépendante des modules métier

### 4. Démo Simple (`demo.py`)
- ✅ Interface basique pour tests rapides
- ✅ Minimal et léger

## 🎛️ Fonctionnalités

### Interface Principal - Onglet Conversion
- **URL TikTok** : Saisie de l'URL à convertir
- **Prévisualisation** : Aperçu avant traitement
- **Métadonnées YouTube** :
  - Titre personnalisé
  - Description détaillée
  - Tags optimisés SEO
  - Catégorie YouTube
- **Options avancées** :
  - Génération automatique des métadonnées
  - Amélioration de la qualité vidéo
  - Ajout de watermark

### Onglet Configuration
- **Authentification YouTube** : Configuration API
- **Paramètres de qualité** : 1080p, 720p, 480p, Auto
- **Dossier de téléchargement** : Sélection personnalisée

### Onglet Historique
- **Suivi des conversions** : Liste des traitements effectués
- **Statistiques** : Métriques de performance

## 🎨 Design et Thème

### Palette de couleurs
- **Arrière-plan** : Noir profond avec dégradés
- **Surface** : Effets glassmorphism avec transparence
- **Primaire** : Violet (#8b5cf6) 
- **Secondaire** : Cyan (#06b6d4)
- **Accent** : Rose (#ec4899)

### Effets visuels
- **Glassmorphism** : Transparence et flou d'arrière-plan
- **Dégradés** : Transitions colorées modernes
- **Animations** : Effets hover et transitions fluides
- **Typographie** : Segoe UI avec hiérarchie claire

## 🔧 Configuration Technique

### Prérequis système
- **Python** : 3.9+ recommandé
- **PyQt6** : 6.6.0+
- **Mémoire** : 2GB RAM minimum
- **Espace disque** : 500MB pour l'environnement virtuel

### Variables d'environnement
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
export QT_SCALE_FACTOR=1.0  # Optionnel pour l'échelle UI
```

### Configuration YouTube API
1. Créer un projet sur Google Cloud Console
2. Activer l'API YouTube Data v3
3. Télécharger le fichier `client_secret.json`
4. Placer le fichier dans le répertoire racine du projet

## 🐛 Dépannage

### Erreurs courantes

**1. "PyQt6 not found"**
```bash
pip install PyQt6>=6.6.0
```

**2. "Modules t2y non trouvés"**
- Normal en mode démo
- Vérifier la structure du projet pour le mode production

**3. "Unknown CSS property warnings"**
- Avertissements cosmétiques sans impact fonctionnel
- Utiliser `main_optimized.py` pour les éviter

**4. Erreur d'authentification YouTube**
- Vérifier le fichier `client_secret.json`
- Renouveler les tokens OAuth2

### Logs et debugging
```bash
# Activation des logs détaillés
export QT_LOGGING_RULES="qt.qpa.xcb.debug=true"
python main_optimized.py
```

## 📈 Performances

### Optimisations implémentées
- **Threading** : Traitement en arrière-plan
- **Cache UI** : Réutilisation des composants
- **Mémoire** : Gestion automatique des ressources
- **CSS optimisé** : Propriétés compatibles PyQt6 uniquement

### Métriques de performance
- **Démarrage** : < 3 secondes
- **Utilisation mémoire** : ~150MB en fonctionnement
- **Traitement vidéo** : Dépend de la taille du fichier

## 🤝 Contribution

### Structure de développement
```bash
# Environnement de développement
python -m venv .venv-dev
source .venv-dev/bin/activate
pip install -r requirements-dev.txt  # si disponible
```

### Conventions de code
- **PEP 8** : Style Python standard
- **Type hints** : Annotations de type recommandées
- **Docstrings** : Documentation des fonctions
- **Tests** : Tests unitaires avec pytest

## 📝 Changelog

### Version 1.0.0 (Actuelle)
- ✅ Interface PyQt6 moderne complète
- ✅ Système d'onglets avancé
- ✅ Styles CSS optimisés
- ✅ Threading pour traitement asynchrone
- ✅ Configuration YouTube intégrée
- ✅ Mode démo pour tests
- ✅ Scripts de lancement automatiques

### Versions futures prévues
- 🔮 v1.1.0 : Batch processing multiple vidéos
- 🔮 v1.2.0 : Éditeur vidéo intégré
- 🔮 v1.3.0 : Planification d'uploads
- 🔮 v2.0.0 : Support d'autres plateformes

## 📞 Support

- **Issues** : GitHub Issues pour bugs et demandes
- **Documentation** : Ce fichier README complet
- **Communauté** : Discussions GitHub

---

**🎉 Félicitations !** Vous avez maintenant une application desktop moderne et fonctionnelle pour convertir vos vidéos TikTok en contenu YouTube professionnel.

*Développé avec ❤️ en PyQt6*