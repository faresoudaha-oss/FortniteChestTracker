# Fortnite Chest Tracker

Application Windows 10/11 (Python + PySide6) qui lit les rediffusions `.replay` enregistrées localement par
Fortnite, après la partie, et affiche des statistiques et un petit overlay. Elle ne lit pas la mémoire du jeu,
n'injecte rien, ne modifie aucun fichier du jeu, ne contacte pas Epic Games et n'automatise rien.

## État du projet
| Élément | Statut |
|---|---|
| Interface (tableau de bord, historique, analyse, paramètres), overlay, tray, notifications | Écrit, démarrage vérifié hors écran sous Linux ; **non testé sous Windows** |
| Base SQLite, surveillance du dossier (attente de fin d'écriture), anti-doublon, analyse manuelle | Tests automatiques réussis (`tests/`, fichiers .replay synthétiques) |
| Lecture de l'en-tête .replay | D'après la documentation du format ; **non validée sur de vrais replays Fortnite** |
| **Détection des coffres** | **Non fournie** : module externe requis, voir `docs/PARSER.md`. Sans lui : « indisponible », rien n'est inventé |
| `.exe` et installateur | Scripts prêts ; **à compiler via GitHub Actions** (non compilés ici) |

## Obtenir les .exe (GitHub Actions)
1. Créez un dépôt GitHub et poussez ce dossier (`git init`, `git add .`, `git commit`, `git push`).
2. Onglet **Actions** > « Build Windows » (se lance au push, ou « Run workflow »).
3. Le workflow exécute les tests, compile avec PyInstaller, lance l'exe en `--selftest`, puis crée l'installateur Inno Setup.
4. Téléchargez l'artefact **FortniteChestTracker** : `FortniteChestTracker.exe` et `FortniteChestTracker-Setup.exe`.

## Compiler à la main (Windows)
    pip install -r requirements-dev.txt
    python tools/make_icon.py
    pyinstaller --noconfirm --clean FortniteChestTracker.spec     (-> dist\FortniteChestTracker.exe)
    iscc installer\FortniteChestTracker.iss                       (-> dist\FortniteChestTracker-Setup.exe)

## Lancer depuis les sources
    pip install -r requirements.txt
    python main.py            # tests : python -m pytest -q tests

## Données et limites
- Statistiques et réglages : `%APPDATA%\FortniteChestTracker` (conservés à la fermeture et à la mise à jour).
- Dossier des replays par défaut : `%LOCALAPPDATA%\FortniteGame\Saved\Demos` (modifiable). Fortnite doit enregistrer les replays (option de jeu).
- L'overlay fonctionne en **plein écran fenêtré** ; pas en plein écran exclusif.
- Fermer la fenêtre réduit l'app dans la zone de notification ; « Quitter » est dans son menu.
- Les anciennes rediffusions sont analysées au démarrage (analyse automatique) ou via l'onglet Analyse.

## Architecture
`fct/replay_header.py` (format) · `fct/analyzer.py` (moteur + contrat du parseur) · `fct/scanner.py` (surveillance)
· `fct/db.py` (SQLite) · `fct/controller.py` (orchestration, thread unique) · `fct/ui/` (PySide6).
