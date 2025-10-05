# 🎨 TikTok to YouTube Desktop • Modern Edition

Une application de bureau moderne avec une direction artistique sombre et des dégradés inspirés par les interfaces contemporaines.

## ✨ Fonctionnalités

### 🎵 Interface Moderne
- **Design sombre élégant** avec dégradés violets/bleus/cyan
- **Animations fluides** et effets de brillance (glow)
- **Composants personnalisés** avec coins arrondis
- **Typographie moderne** (Segoe UI, SF Pro Display, Inter)
- **Interface responsive** qui s'adapte à différentes tailles d'écran

### 🚀 Fonctionnalités Métier
- **Téléchargement TikTok** avec aperçu en temps réel
- **Upload YouTube automatisé** avec toutes les options
- **Préremplissage intelligent** des métadonnées
- **Gestion des Shorts** (détection automatique < 60s)
- **Options avancées** : tags, catégories, langues, etc.
- **Barres de progression animées** pour le téléchargement et l'upload

## 🛠️ Installation

### Prérequis
- Python 3.9+
- PyQt6
- Modules existants du projet (t2y/)

### Installation rapide
```bash
# Lancer le script d'installation et de démarrage
./launch_desktop.sh
```

### Installation manuelle
```bash
# Créer l'environnement virtuel
python3 -m venv .venv-desktop
source .venv-desktop/bin/activate

# Installer les dépendances
pip install PyQt6
pip install -r requirements.txt

# Lancer l'application
python desktop_app/main.py
```

## 🎯 Utilisation

1. **Lancez l'application** via le script `./launch_desktop.sh`
2. **Collez l'URL TikTok** dans le champ prévu
3. **Cliquez sur "Préremplir"** pour récupérer automatiquement les métadonnées
4. **Ajustez les informations** YouTube (titre, description, visibilité)
5. **Configurez les options avancées** si nécessaire
6. **Cliquez sur "Lancer le traitement"** et observez la progression

## 🎨 Direction Artistique

### Palette de Couleurs
- **Fond principal** : Dégradé noir (#0a0a0a) vers bleu foncé (#1a1a2e)
- **Primary** : Violet (#8b5cf6)
- **Secondary** : Cyan (#06b6d4)  
- **Accent** : Rose (#ec4899)
- **Surface** : Glassmorphism avec transparence
- **Texte** : Blanc (#ffffff) et gris clair (#a1a1aa)

### Effets Visuels
- **Glassmorphism** : Fond transparent avec bordures subtiles
- **Dégradés animés** : Sur les boutons et barres de progression
- **Effets de brillance** : Au survol des éléments interactifs
- **Coins arrondis** : 12-20px selon les éléments
- **Ombres douces** : Pour la profondeur et l'élévation

## 📁 Structure du Projet

```
desktop_app/
├── main.py              # Point d'entrée principal
├── demo.py              # Version de démonstration
├── ui/
│   ├── __init__.py
│   ├── main_window.py    # Fenêtre principale
│   ├── components.py     # Composants personnalisés
│   └── styles.py         # Thèmes et styles CSS
└── assets/              # Ressources (icônes, images)
```

## 🔧 Développement

### Composants Personnalisés
- `GradientProgressBar` : Barre de progression avec dégradé animé
- `AnimatedButton` : Bouton avec effets de brillance
- `StatusCard` : Carte d'état avec différents types (info, success, warning, error)
- `LoadingSpinner` : Spinner de chargement animé
- `ImagePreview` : Aperçu d'image avec placeholder élégant
- `MetricsCard` : Carte pour afficher des métriques

### Ajout de Nouvelles Fonctionnalités
1. Créer le composant dans `ui/components.py`
2. Ajouter les styles dans `ui/styles.py`
3. Intégrer dans `ui/main_window.py`
4. Tester avec la version de démonstration

## 🚨 Dépannage

### L'application ne se lance pas
- Vérifiez que PyQt6 est installé : `pip list | grep PyQt6`
- Assurez-vous d'être dans le bon répertoire
- Utilisez le script `./launch_desktop.sh` pour un diagnostic automatique

### Erreurs de modules manquants
- Vérifiez que l'environnement virtuel est activé
- Installez les dépendances : `pip install -r requirements.txt`
- Vérifiez les chemins d'importation dans le code

### Interface qui ne s'affiche pas correctement
- Les styles CSS peuvent ne pas être compatibles avec votre version de PyQt6
- Utilisez la version de démonstration pour tester : `python desktop_app/demo.py`

## 🔮 Roadmap

### Version 2.1
- [ ] Mode sombre/clair avec commutateur
- [ ] Thèmes personnalisables
- [ ] Raccourcis clavier
- [ ] Glisser-déposer de fichiers

### Version 2.2
- [ ] File d'attente avec traitement en lot
- [ ] Historique des uploads
- [ ] Statistiques et métriques
- [ ] Export vers d'autres plateformes

### Version 2.3
- [ ] Plugins et extensions
- [ ] API REST intégrée
- [ ] Interface web complémentaire
- [ ] Mode portable (executable unique)

## 📄 License

Ce projet utilise la même licence que le projet principal TikTok-to-Youtube.

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche pour votre fonctionnalité
3. Commitez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

## 💡 Inspiration

Cette interface s'inspire des tendances actuelles du design d'interface :
- **Glassmorphism** popularisé par Apple
- **Dark mode** omniprésent dans les applications modernes
- **Dégradés vibrants** style Discord/Spotify
- **Animations fluides** pour une meilleure UX

---

*Développé avec ❤️ en utilisant PyQt6 et beaucoup de CSS custom*