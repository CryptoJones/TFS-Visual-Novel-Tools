# TFS Visual Novel Tools

A book-agnostic toolkit for turning a book you own — or one in the public domain —
into an illustrated point-and-click adventure game / visual novel. It's the pipeline
behind *The Flatline Sessions* trilogy, carved out so anyone can reuse it.

**You bring the source material and the art. The toolkit gives you the engine, the
pipeline, and the art book.** It ships **no copyrighted text or art** — the example
lineage lives in its own repos; this is just the machinery.

## What's in the box

1. **Godot adventure engine** (`engine/`) — a data-driven room / chapter / dialog / save
   engine (Godot 4.6). Rooms + exits + NPCs + inventory + a dedication card, title/menu,
   fixed compass, and autosave — all driven by JSON and a `backgrounds_hd/` folder.
   **✅ Carved and runnable: a two-room demo plays out of the box — see
   [`engine/README.md`](engine/README.md).**
2. **Art-book generator** (`tools/artbook/build_artbook.py`) — turns a folder of
   background plates + an index into a clean 16:9 landscape PDF art book (full-bleed
   cover, art-only plate pages, closing dedication). *(carried over working; needs
   config-driving so it isn't hardcoded to specific repos — see PLAN.md)*
3. **GUI configurator** (`tools/configurator/`) — a small desktop app: point it at your
   generated background plates + a scene config, and it scaffolds a ready-to-run Godot
   project. For people who already have assets and just want to drop them into an engine.
   *(to build — see PLAN.md)*
4. **Prompt-craft guide** (`docs/PROMPT-CRAFT.md`) — how to generate clean background
   plates on a local flux2 / ComfyUI pipeline *without* the "AI slop" tells: garbled
   text, inserted bodies, phantom walls, botched duplicates. *(to write — see PLAN.md)*

## The workflow

1. Pick your book (public domain, or one you own). Break it into rooms / chapters.
2. Engineer scene prompts (see the prompt-craft guide) and generate background plates.
3. Run the configurator — or hand-edit the data JSON — to wire assets → engine.
4. Play it. Generate the art-book PDF.

## License

Apache License 2.0 — see [LICENSE](LICENSE). © 2026 CryptoJones.

## Status

The **Godot engine is carved and runnable** (`engine/`) — a two-room demo plays out of
the box with the full feature set (dedication card, fixed compass, autosave, saves,
dialog, inventory). The art-book generator is in place. Still on the roadmap:
config-driving the generator, the GUI configurator, and the prompt-craft guide — see
[PLAN.md](PLAN.md).
