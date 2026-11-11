# Module de détection des coffres

Le tracker lit lui-même l'en-tête des `.replay` (durée, date, intégrité, partie terminée).
Le comptage des coffres exige de décoder les canaux réseau Unreal du replay (chunks chiffrés/compressés,
Oodle selon la saison). Cela se fait par un **module externe** que l'application appelle :

    <commande> <fichier.replay>      ->  JSON sur stdout (UTF-8), code de sortie 0

```json
{"mode": "Solo", "player": "Pseudo",
 "events": [{"t_ms": 183000, "kind": "standard", "action": "opened", "actor": "player", "certain": true}]}
```

- `kind` : `standard`, `rare`, `enterre`, `special`, `sprite`
- `action` : `opened` ou `destroyed`
- `actor` : `player`, `teammate`, `enemy`, `unknown`
- `certain` : `false` si l'attribution au joueur est incertaine

Seules les actions `actor == "player"` sont comptées. Un `unknown` ou un `certain: false` rend la partie « incertaine ».
Sans module configuré, la partie est marquée « indisponible » et **aucun coffre n'est compté**.

Laisser vide dans Paramètres pour utiliser le module fourni.

## État actuel
Le module fourni est `replay-exporter` (C#, .NET), compilé en `bin/ReplayExporter.exe` et embarqué dans l'application. Il réutilise
`ReplayAnalyzer.cs` du projet LED-N/Fortnite-ChestCounter (MIT) et renvoie le JSON ci-dessus. Champs supplémentaires :
`battle_royale` (faux = partie ignorée), `ammo_boxes`, `blueprint` (nom technique du coffre).
Exécuté sur 3 vrais replays : voir README. L'exactitude des comptes n'est pas encore vérifiée face à un décompte réel.
Un autre module peut être utilisé via Paramètres, tant qu'il respecte ce contrat.
