# TFS Visual Novel Tools

A book-agnostic toolkit for turning a book you own — or one in the public domain —
into an illustrated point-and-click adventure game / visual novel. It's the pipeline
behind *The Flatline Sessions* trilogy, carved out so anyone can reuse it.

**You bring the source material and the art. The toolkit gives you the engine, the
wizard, the CLI backend, and the art book.** It ships **no copyrighted text or art** —
the example lineage lives in its own repos; this is just the machinery.

## Quick start

```sh
python3 -m pip install -e .
tfs-vn demo --out /tmp/tfs-vn-demo
godot --path /tmp/tfs-vn-demo
```

For the desktop wizard:

```sh
tfs-vn wizard
```

For a real project, write `project.json` or use the wizard, then run:

```sh
tfs-vn scaffold --config project.json --out ./build/my-game
```

## What's in the box

1. **Godot adventure engine** (`engine/`) — a data-driven room / chapter / dialog / save
   engine (Godot 4.6). Rooms + exits + NPCs + inventory + a dedication card, title/menu,
   fixed compass, and autosave — all driven by JSON and a `backgrounds_hd/` folder.
   **✅ Carved and runnable: a two-room demo plays out of the box — see
   [`engine/README.md`](engine/README.md).**
2. **CLI backend** (`tfs-vn`) — scaffolds projects, validates generated Godot data,
   emits a demo project, and builds art books from config files.
3. **GUI configurator** (`tools/configurator/`) — a Tkinter desktop wizard: point it at
   generated background plates, create rooms, and scaffold a ready-to-run Godot project.
4. **Art-book generator** (`tfs-vn artbook`) — turns a folder of background plates +
   config/index metadata into a clean 16:9 landscape PDF art book.
5. **Prompt-craft guide** (`docs/PROMPT-CRAFT.md`) — how to generate clean background
   plates on a local flux2 / ComfyUI pipeline *without* the "AI slop" tells: garbled
   text, inserted bodies, phantom walls, botched duplicates.

## The workflow

1. Pick your book (public domain, or one you own). Break it into rooms / chapters.
2. Engineer scene prompts (see the prompt-craft guide) and generate background plates.
3. Run the configurator — or hand-edit `project.json` — to wire assets → engine.
4. Play it. Generate the art-book PDF.

## License

Apache License 2.0 — see [LICENSE](LICENSE). © 2026 CryptoJones.

## Status

The **Godot engine is carved and runnable** (`engine/`) and the reusable CLI/wizard
layer is in place. See [docs/CLI.md](docs/CLI.md), [docs/CONFIG.md](docs/CONFIG.md),
and [docs/PROMPT-CRAFT.md](docs/PROMPT-CRAFT.md).
