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

## 2. Config-drive the art-book generator (`tools/artbook/build_artbook.py`)
Today its `BOOKS` dict hardcodes specific repo paths. Change it to take a config file /
CLI args: `--repo`, `--title`, `--subtitle`, `--cover`, `--title-screen`, `--dedication`,
`--accent`, `--out`. Then anyone can point it at their own project. Keep the art-only +
dedication + full-bleed-cover features that already work.

## 3. Build the GUI configurator (`tools/configurator/`)
A small desktop app (tkinter or PyQt — dependency-light). Inputs: a folder of background
plates + a scene/chapters config (or a wizard that builds one). Output: a scaffolded,
ready-to-run Godot project — copies the `engine/` template, drops the plates into
`assets/backgrounds_hd/`, writes the `data/*.json`. The "I already generated my art, just
give me a game" one-click path. This is the token-saver.

## 4. Write the prompt-craft guide (`docs/PROMPT-CRAFT.md`)
The book-agnostic slop-avoidance rules for local flux2 / ComfyUI plate generation:
positive-only prompts (cfg 1 zeroes the negative), never name signs/posters/screens/"a
title" (garbled text), never imply a person (body-horror), singularize plural objects,
a separate exterior suffix so "blank smooth walls" doesn't hallucinate walls outdoors,
and the tipped-furniture-backs trick for ransacked/complex rooms.

## 5. Publish
Create the public GitHub repo (needs CryptoJones's go), push, tag an initial release.
Apache 2.0.
