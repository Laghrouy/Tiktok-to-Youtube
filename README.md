# TikTok → YouTube Uploader (Tk)

Application de bureau (Tkinter + ttkbootstrap) pour télécharger des vidéos TikTok (yt-dlp) et les publier sur YouTube (API officielle), avec profils, file d’attente, options avancées et mode headless.

## Sommaire
- Pré-requis
- Installation & lancement
- Authentification Google (OAuth)
- Profils YouTube (multi-comptes)
- Utilisation rapide
- File d’attente & reprise
- Options avancées (Proxy, Timeout, Chunk, Retries, ffmpeg)
- Surveillance TikTok (poll)
- Raccourcis clavier
- Export diagnostic
- Dépannage

## Pré-requis
- Python 3.10+
- Dépendances (requirements.txt)
- Tkinter (Linux: `sudo apt install python3-tk`)
- Un fichier `client_secret.json` (identifiants OAuth 2.0 « Desktop App »)

## Installation & lancement
1) Placez `client_secret.json` à la racine du projet.
2) Exécutez le lanceur Tk (crée l’environnement si besoin):
   - Linux/macOS: `./launch_tk.sh`
3) Le script configure `.venv-desktop`, installe les dépendances et lance l’UI.

Headless (serveur sans GUI): le lanceur active un mode d’authentification console si aucune session graphique n’est détectée (env `T2Y_NO_BROWSER=1`).

## Authentification Google (OAuth)
- Le premier lancement ouvre un navigateur local (ou console en headless) pour accorder les droits.
- Les tokens sont stockés par profil sous `~/.config/tiktok-to-youtube/tokens/`.
- Bouton “Déconnecter/Re-auth” pour supprimer le token et forcer une reconnexion.

## Profils YouTube (multi-comptes)
- Sélection dans l’UI (combobox “Profil YouTube”).
- Boutons: Charger, Enregistrer, Dupliquer, Supprimer (supprime aussi le token associé), Exporter/Importer en JSON.

## Utilisation rapide
1) Collez l’URL TikTok et un Titre YouTube. Cliquez “Préremplir” pour récupérer titre/description/miniature depuis TikTok.
2) Ajustez Description et Visibilité. Facultatif: tags, catégorie, langue, madeForKids, licence, géoloc, date d’enregistrement, playlists, planification.
3) Lancez “▶ Lancer”. Suivez la progression (download/upload). En cas d’échec, consultez le “Journal”.

Shorts: si la vidéo est verticale et <60s, on ajoute le tag “Shorts” et `#Shorts`. Option de recadrage 9:16 pour forcer le format short.

## File d’attente & reprise
- Ajoutez des items (URL[,titre]) via “Ajouter” ou “Importer…” (TXT/CSV).
- Persistance: `queue.json` sous `~/.config/tiktok-to-youtube/`.
- Reprise au démarrage: les items “terminé” ne sont pas relancés; les erreurs peuvent être relancées via “Reprendre erreurs”.
- Contrôles: Démarrer, Pause/Resume, Vider terminés, Monter/Descendre, Reprendre erreurs.
- Pause après N vidéos: cochez l’option dans la toolbar et indiquez N; la file se met automatiquement en pause après N items.

## Options avancées
- Réseau: Timeout upload (s), Proxy (http/https), Test “Connexion YouTube” (GET API public), indicateur de proxy actif (UI/ENV masqué).
- Upload: Chunk (MB) et Retries (backoff exponentiel + jitter). Chunk arrondi au multiple de 256KB comme requis par l’API.
- Tags: limitation automatique à 500 caractères cumulés (YouTube) avec déduplication.
- ffmpeg: détection automatique, bouton “Choisir ffmpeg…” (chemin personnalisé), affichage version/chemin.
- Traitements vidéo (facultatifs): recadrage 9:16, padding, normalisation audio, remux (faststart), trim, watermark (position/opacité).

## Surveillance TikTok (poll)
- Saisissez un profil TikTok (URL ou @handle). Définissez l’intervalle (min), filtres durées et mots-clés, et un quota par poll.
- Démarrer/Arrêter. Les nouvelles vidéos passent dans la file si elles passent les filtres.
- Dernier poll: horodatage affiché. Option “Démarrer au lancement” avec persistance.

## Raccourcis clavier
- Ctrl+L: Lancer
- Ctrl+Shift+C: Copier les logs
- Ctrl+O: Ouvrir dossier logs
- Ctrl+P: Préremplir depuis TikTok

## Export diagnostic
- Bouton “Exporter diagnostic” dans le Journal: archive ZIP contenant logs, settings, profiles, queue, versions Python/packages, ffmpeg, proxies.

## Dépannage
- Auth 401: utilisez “Déconnecter/Re-auth” (supprime le token et relance l’OAuth), vérifiez `client_secret.json`.
- Réseau/Proxy: testez la connexion depuis Options avancées; fournissez le proxy dans l’UI si nécessaire.
- yt-dlp: mettez à jour yt-dlp; vérifiez l’URL TikTok et la disponibilité publique.
- ffmpeg: si non détecté, utilisez “Choisir ffmpeg…” ou installez `ffmpeg` via votre gestionnaire de paquets.

## Sécurité
- Ne partagez pas `client_secret.json` ni les tokens.
- Respectez la propriété intellectuelle et les CGU des plateformes.

## Licence
Projet éducatif. Voir le dépôt pour les détails.
