# Fortnite Chest Tracker

Application Windows 10/11 (Python + PySide6) qui lit les rediffusions `.replay` enregistrées localement par
Fortnite, après la partie, et affiche des statistiques et un petit overlay. Elle ne lit pas la mémoire du jeu,
n'injecte rien, ne modifie aucun fichier du jeu, ne contacte pas Epic Games et n'automatise rien.

## État du projet
| Élément | Statut |
|---|---|
| Interface (tableau de bord, historique, analyse, paramètres), overlay, tray, notifications | Écrit, démarrage vérifié hors écran sous Linux ; **non testé sous Windows** |
| Base SQLite, surveillance du dossier (attente de fin d'écriture), anti-doublon, analyse manuelle | Tests automatiques réussis (`tests/`) |
| Lecture de l'en-tête .replay | **Validée sur 3 vrais replays Fortnite** (décembre 2025) |
| Détection des coffres (module .NET `replay-exporter`, basé sur le décodeur de LED-N) | **Exécutée sur 3 vrais replays** (sous Linux) : ~1 à 4 s par fichier, coffres ouverts/détruits, mode, joueur. **Exactitude des chiffres non vérifiée** face à un comptage réel |
| Compilation Windows du module, `.exe` et installateur | Scripts prêts ; **à compiler via GitHub Actions** (jamais exécutés) |

Ne sont comptés que les coffres du joueur qui a enregistré le replay, en Battle Royale. Les caisses de munitions ne sont pas
dans le total des coffres. Sprite : « coffres d'esprit » (reliques/affiches), classés « sprite ».

## Obtenir les .exe (GitHub Actions)
1. Créez un dépôt GitHub et poussez ce dossier (`git init`, `git add .`, `git commit`, `git push`).
2. Onglet **Actions** > « Build Windows » (se lance au push, ou « Run workflow »).
3. Le workflow télécharge le décodeur open source, compile le module .NET, exécute les tests, compile avec PyInstaller, lance l'exe en `--selftest`, puis crée l'installateur Inno Setup.
4. Téléchargez l'artefact **FortniteChestTracker** : `FortniteChestTracker.exe` et `FortniteChestTracker-Setup.exe`.

## Compiler à la main (Windows)
    git clone https://github.com/LED-N/Fortnite-ChestCounter third_party/upstream   (puis checkout du commit de third_party/UPSTREAM_COMMIT.txt)
    dotnet publish replay-exporter/ReplayExporter.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:EnableCompressionInSingleFile=true -p:DebugType=none -o bin
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
`replay-exporter/` (module .NET de lecture des replays) · `fct/replay_header.py` (format) · `fct/analyzer.py` (moteur + contrat du parseur) · `fct/scanner.py` (surveillance)
· `fct/db.py` (SQLite) · `fct/controller.py` (orchestration, thread unique) · `fct/ui/` (PySide6).

## Crédits et licences
Lecture des replays : [Fortnite-ChestCounter](https://github.com/LED-N/Fortnite-ChestCounter) de LED-N (MIT), basé sur
[FortniteReplayDecompressor](https://github.com/Shiqan/FortniteReplayDecompressor) de Shiqan (MIT). Leurs licences sont
copiées dans `licences\` par l'installateur et doivent rester avec toute version distribuée. Projet non affilié à Epic Games.
