# Config Files

The toolkit has two user-facing JSON configs: `project.json` for scaffolding a
Godot game and `artbook.json` for building the PDF art book.

## project.json

Minimal example:

```json
{
  "title": "My Adventure",
  "subtitle": "A Visual Novel",
  "dedication": "For the readers.",
  "accent": "#37d2c3",
  "assets": {
    "backgrounds": "plates",
    "cover": "cover.png"
  },
  "chapters": [
    {
      "id": "chapter_1",
      "title": "Chapter 1",
      "pov": "protagonist",
      "pov_name": "Protagonist",
      "rooms": [
        {
          "id": "foyer",
          "name": "Foyer",
          "desc": "A quiet entry hall.",
          "bg": "foyer"
        },
        {
          "id": "study",
          "name": "Study",
          "desc": "A study lined with books.",
          "bg": "study"
        }
      ]
    }
  ]
}
```

If no exits are supplied, the scaffold links rooms linearly west/east. To author
your own graph, add exits:

```json
{ "exits": { "east": "study", "north": "stairs" } }
```

Room fields:

- `id`, `name`, `desc`
- `bg`: plate id copied from `assets.backgrounds/<bg>.png`
- `plate`, `image`, or `bg_file`: explicit image file path
- `exits`: `west`, `north`, `south`, `east`
- `npcs`, `pickups`, `shop`, `net`, `matrix`, `music`
- `on_enter_flag`, `requires_flag`, `locked_text`

Optional top-level objects:

- `npcs`
- `items`
- `quests`
- `shops`
- `cyberspace`
- `pax`
- `bundle_id`
- `binary_name`

The generated project writes the existing Godot engine files under `data/`:

- `data/chapters.json`
- `data/rooms/*.json`
- `data/npcs/*.json`
- `data/quests.json`
- `data/items.json`
- `data/shops.json`

## artbook.json

Explicit plate list:

```json
{
  "title": "The Art of My Adventure",
  "subtitle": "A Visual Novel",
  "out": "The_Art_of_My_Adventure.pdf",
  "accent": "#37d2c3",
  "dedication": "For the readers.",
  "cover": "cover.png",
  "title_screen": "title.png",
  "asset_dir": "plates",
  "plates": [
    {
      "plate": "P001",
      "type": "room",
      "source": "foyer.png",
      "caption": "The foyer.",
      "prompt": "A quiet entry hall."
    }
  ]
}
```

Index-based plate list:

```json
{
  "repo": ".",
  "index": "docs/art-review-index.md",
  "title": "The Art of My Adventure",
  "subtitle": "A Visual Novel",
  "out": "docs/artbook.pdf",
  "accent": "#37d2c3",
  "manifests": ["scratchpad/manifest.json"]
}
```

When `plates` is present, `source` paths resolve relative to `asset_dir` if set.
When using an index, source paths resolve relative to `repo`.
