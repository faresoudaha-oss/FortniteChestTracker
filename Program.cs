// Lit un .replay (en lecture seule) et écrit sur stdout le JSON décrit dans docs/PARSER.md.
using System.Text.Json;
using ChestCounter;

if (args.Length < 1) { Console.Error.WriteLine("usage: ReplayExporter <fichier.replay>"); return 2; }
try
{
    using var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
    var m = new ReplayAnalyzer().Analyze(fs, args[0], null);   // null = joueur qui a enregistré le replay
    static string Kind(string k, string bp)
    {
        k = ChestKinds.Canonical(k);
        var b = bp.ToLowerInvariant();
        if (k == ChestKinds.Normal) return "standard";
        if (k == ChestKinds.Rare) return "rare";
        if (k == ChestKinds.Buried) return "enterre";
        if (k == ChestKinds.Extraction || k == ChestKinds.PosterChest) return "sprite";
        return "special";
    }
    var events = m.Chests.Select(c => new
    {
        t_ms = (int)(c.TimeSeconds * 1000),
        kind = Kind(c.Kind, c.Blueprint),
        action = c.Destroyed ? "destroyed" : "opened",
        actor = "player",
        certain = true,
        blueprint = c.Blueprint,
    });
    var o = new
    {
        mode = m.Playlist ?? "Inconnu",
        player = m.PlayerName ?? "",
        battle_royale = m.IsBattleRoyale,
        duration_s = m.DurationSeconds,
        ammo_boxes = m.AmmoBoxesOpened,
        events,
    };
    Console.OutputEncoding = new System.Text.UTF8Encoding(false);
    Console.WriteLine(JsonSerializer.Serialize(o));
    return 0;
}
catch (Exception e)
{
    Console.Error.WriteLine(e.GetType().Name + ": " + e.Message);
    return 1;
}
