# Prompt Craft for Background Plates

These rules are for generating clean visual novel background plates before you
wire them into the toolkit.

- Write positive prompts. With low-CFG local workflows, negative prompts may do
  little or nothing.
- Do not ask for readable signs, posters, screens, labels, book titles, or wall
  text unless you plan to repaint them yourself.
- Do not imply people if the room should be empty. Avoid phrasing like "where
  someone was sitting" or "a worker's desk" when no body should appear.
- Prefer singular objects when composition matters. "A chair" is easier to
  control than "chairs" when the generator tends to duplicate or melt forms.
- Use a separate exterior suffix. Interior safety phrases like "blank smooth
  walls" can create walls outdoors.
- For ransacked rooms, ask for furniture backs, tipped cabinets, spilled drawers,
  and scattered papers instead of vague "chaos."
- Keep title and cover art free of generated lettering. Let the engine render
  the actual title on top.
- Treat every accepted plate name as an API. Stable filenames make JSON, artbook
  config, and regeneration work predictable.
