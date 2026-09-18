# TFS Visual Novel Engine

A small, data-driven **Godot 4** engine for point-and-click adventures / visual
novels, carved from *The Flatline Sessions* games. You bring the words and art;
the engine runs the loop.

It ships **asset-light**: everything is playable as a scaffold before you add a
single plate or track. Drop a folder of background images in and write some
JSON, and you have a game.

## What it does

- **Studio ident → title → chapter select → explore → dialog → menu** state
  machine, plus a fade-in **dedication** card before the title. The ident card
  is skipped cleanly when its art is absent.
- **Rooms + exits** with a fixed **W/N/S/E compass** (directions that aren't
  exits are dimmed, not hidden).
- **Branching dialog**, an **inventory / shops / economy**, an optional
  **cyberspace** mini-game, and an optional **NET** terminal.
- **Give Hint** — a per-room button (and the `H` key) that maps the compass
  route to the current objective and names the action to take; finished
  conversations drop their Talk button to keep the action bar tidy.
- **Autosave on by default** (rolling slot) plus manual multi-slot saves,
  quicksave/quickload, and a Settings panel (music + autosave toggles).
- A full-bleed **title cover** with the game name overlaid, and a quiet
  anti-tamper "void" room for hacked saves.
- **Crossfading music** with per-area cues (a room's `music` key wins, then
  shops, then the chapter's cue). Every cue opens at a **randomised,
  hypermeasure-aligned entry point** so revisits don't replay the same opening.

Everything degrades gracefully: a missing plate shows a tinted placeholder, a
missing track plays silence.

## Run it

```sh
godot --path .            # play the two-room demo
godot --headless --path . --script res://tests/validate_data.gd   # data check
godot --headless --path . --script res://tests/playthrough.gd     # reachability
```

## Make it yours

1. Use the toolkit CLI/wizard to generate the project:

   ```sh
   tfs-vn scaffold --config project.json --out ./build/my-game
   ```

2. **Content** lives entirely in `data/`:
   - `chapters.json` — the title (`game`), the `dedication` card text (empty =
     skip it), and the chapter list.
   - `data/rooms/<chapter>.json` — rooms, exits, npcs, pickups, flags.
   - `data/npcs/<id>.json` — branching dialog.
   - `quests.json`, `items.json`, `shops.json`, `data/pax/*.json`,
     `data/cyberspace/databases.json`.
3. **Art** goes in `assets/backgrounds_hd/<bg>.png` (referenced by a room's
   `"bg"`), `assets/ui/cover.png` (title cover), and `assets/audio/music/*.ogg`.
   The optional studio ident is `assets/ui/ronin48_games_studio.png`. The
   scaffold empties `assets/ui/`, `assets/backgrounds_hd/` and
   `assets/audio/music/`, so ship those files from your game repo.
4. **Branding**: rename `config/name` in `project.godot`, change the one accent
   color in `src/ui/UITheme.gd`, and set the export binary names + bundle id in
   `export_presets.cfg`.

The two-room demo in `data/` is a working reference for every field.

## License

Apache-2.0, © CryptoJones. Ships no third-party content — bring your own.
