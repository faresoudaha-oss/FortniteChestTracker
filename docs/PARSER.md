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

À renseigner dans Paramètres > « Module de détection des coffres ».

## État actuel (honnête)
Ce module n'est **pas fourni et non testé** : je n'ai pas de vrais replays Fortnite. Pistes : parseurs open source
existants (FortniteReplayReader en C#, replay-reader en Node.js) à encapsuler dans un petit exécutable respectant ce contrat.
Il faudra vérifier sur de vrais replays quels événements correspondent à l'ouverture d'un coffre et à son auteur.
