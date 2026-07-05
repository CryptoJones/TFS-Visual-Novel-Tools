# Roadmap

Kickoff done: license (Apache 2.0), README, this plan, and the working art-book
generator. What's left to make this a real reusable toolkit:

## 1. Carve the Godot adventure engine → `engine/` — ✅ DONE (2026-07-03)
Extracted the data-driven engine from the Flatline games (`src/core/Game.gd` state machine:
TITLE / CHAPTERS / EXPLORE / DIALOG / MENU + the DEDICATION card state, rooms + exits +
NPC dialog + inventory + save/load with **autosave**, the fixed **W/N/S/E compass**, and
`UITheme`). Book-specific content stripped; dedication text + game title are config-driven.
Reads `data/*.json` + `assets/backgrounds_hd/*.png`, ships a **two-room demo** that plays
out of the box, `validate_data` + `playthrough` green. Godot 4.6, export presets templated
(binary name + bundle id placeholders). See `engine/README.md`.

## 2. Config-drive the art-book generator (`tools/artbook/build_artbook.py`) — ✅ DONE
The old hardcoded `BOOKS` map is gone. `tfs-vn artbook --config artbook.json` now
drives repo/index paths, explicit plate lists, cover/title-screen art, dedication,
accent, output path, and optional manifests. The legacy script remains as a wrapper.

## 3. Build the GUI configurator (`tools/configurator/`) — ✅ DONE
A dependency-light Tkinter app now collects project metadata, plate folders, rooms,
and output path, then calls the same scaffold backend as the CLI. Generated projects
copy the `engine/` template, copy plates into `assets/backgrounds_hd/`, write
`data/*.json`, and can run the Godot validators.

## 4. Write the prompt-craft guide (`docs/PROMPT-CRAFT.md`) — ✅ DONE
The book-agnostic slop-avoidance rules for local flux2 / ComfyUI plate generation:
positive-only prompts (cfg 1 zeroes the negative), never name signs/posters/screens/"a
title" (garbled text), never imply a person (body-horror), singularize plural objects,
a separate exterior suffix so "blank smooth walls" doesn't hallucinate walls outdoors,
and the tipped-furniture-backs trick for ransacked/complex rooms.

## 5. Harden packaging and examples
Next polish lane: wheel packaging that embeds or locates the engine template outside a
source checkout, richer wizard editing for branching exits/dialog, and release artifacts.

## 6. Publish
Create the public GitHub repo (needs CryptoJones's go), push, tag an initial release.
Apache 2.0.
