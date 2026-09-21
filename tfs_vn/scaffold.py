"""Generate a ready-to-run Godot visual novel project from JSON config."""

from __future__ import annotations

import os
from pathlib import Path
import random
import shutil
from typing import Any

from .config import (
    ConfigError,
    as_list,
    as_object,
    engine_template,
    godot_string,
    load_json,
    resolve_path,
    slugify,
    titleize_slug,
    write_json,
)
from .validate import validate_project


DIRECTIONS = ("west", "north", "south", "east")

## Studio ident seeded into every scaffold. It is studio branding rather than
## game art, so it is re-copied after the per-game asset folders are cleared and
## every game shows the ident without copying the file in by hand.
STUDIO_IDENT = Path("assets/ui/ronin48_games_studio.png")


def scaffold_from_config(
    config_path: str | Path,
    out: str | Path | None = None,
    *,
    template: str | Path | None = None,
    force: bool = False,
    run_validation: bool = True,
    godot: str = "godot",
) -> Path:
    src = Path(config_path).expanduser().resolve()
    config = load_json(src)
    return scaffold_project(
        config,
        out or config.get("out"),
        config_dir=src.parent,
        template=template,
        force=force,
        run_validation=run_validation,
        godot=godot,
    )


def scaffold_project(
    config: dict[str, Any],
    out: str | Path | None,
    *,
    config_dir: str | Path,
    template: str | Path | None = None,
    force: bool = False,
    run_validation: bool = True,
    godot: str = "godot",
) -> Path:
    if out in (None, ""):
        raise ConfigError("scaffold output path is required")
    config_dir = Path(config_dir).expanduser().resolve()
    out_dir = Path(out).expanduser()
    if not out_dir.is_absolute():
        out_dir = (config_dir / out_dir).resolve()
    _copy_engine(engine_template(template or os.environ.get("TFS_VN_ENGINE_TEMPLATE")), out_dir, force)
    generated = _generate_project_data(config, config_dir)
    _write_generated_data(out_dir, generated)
    _copy_assets(out_dir, generated)
    _rebrand_project(out_dir, generated)
    if run_validation:
        validate_project(out_dir, godot=godot)
    return out_dir


def example_project_config() -> dict[str, Any]:
    return {
        "title": "Untitled Adventure",
        "subtitle": "A Demo",
        "dedication": "Built with TFS Visual Novel Tools.",
        "accent": "#37d2c3",
        "chapters": [
            {
                "id": "demo",
                "title": "The First Door",
                "pov": "traveler",
                "pov_name": "The Traveler",
                "pov_desc": "A visitor with questions and no easy answers.",
                "intro": ["The room is quiet. The way forward is east."],
                "outro": ["You crossed the threshold."],
                "rooms": [
                    {
                        "id": "foyer",
                        "name": "Foyer",
                        "desc": "A dim entry hall with one open doorway.",
                    },
                    {
                        "id": "study",
                        "name": "Study",
                        "desc": "A small study with a desk, a chair, and an answer waiting.",
                    },
                ],
            }
        ],
    }


def _copy_engine(template: Path, out_dir: Path, force: bool) -> None:
    template = template.resolve()
    out_dir = out_dir.resolve()
    if out_dir == template or template in out_dir.parents:
        raise ConfigError("output directory must not be the engine template or inside it")
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise ConfigError(f"{out_dir} already exists and is not empty; use --force to replace it")
        shutil.rmtree(out_dir)
    shutil.copytree(template, out_dir, ignore=_ignore_template)
    for rel in ("data", "assets/backgrounds_hd", "assets/ui", "assets/audio/music"):
        p = out_dir / rel
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)
        (p / ".gitkeep").write_text("", encoding="utf-8")
    # Re-seed the studio ident the wipe above just removed. Games may replace it
    # with their own file; the engine skips the ident card when it is absent.
    ident = template / STUDIO_IDENT
    if ident.exists():
        dst = out_dir / STUDIO_IDENT
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ident, dst)


def _ignore_template(_dir: str, names: list[str]) -> set[str]:
    ignored = {".godot", "build", ".import"}
    ignored.update(n for n in names if n.endswith((".import", ".uid", ".tmp")))
    return ignored


def _generate_project_data(config: dict[str, Any], config_dir: Path) -> dict[str, Any]:
    title = str(config.get("title") or config.get("game") or "Untitled Adventure").strip()
    subtitle = str(config.get("subtitle") or "").strip()
    game_title = str(config.get("game") or _join_title(title, subtitle))
    accent = _normalize_hex(str(config.get("accent") or "#37d2c3"))
    assets = as_object(config.get("assets"), "assets")
    bg_dir = resolve_path(config_dir, assets.get("backgrounds") or config.get("backgrounds"))
    cover = resolve_path(config_dir, assets.get("cover") or config.get("cover"))
    audio_dir = resolve_path(config_dir, assets.get("audio") or config.get("audio"))

    chapters_in = as_list(config.get("chapters"), "chapters")
    if not chapters_in:
        raise ConfigError("at least one chapter is required")

    npc_defs = _initial_npcs(config)
    items = _initial_collection(config.get("items"), "items")
    shops = _initial_collection(config.get("shops"), "shops")
    quests = _initial_collection(config.get("quests"), "quests")
    chapters_out: list[dict[str, Any]] = []
    room_files: dict[str, dict[str, Any]] = {}
    asset_copies: list[tuple[Path, Path]] = []

    for ch_index, chapter in enumerate(chapters_in, start=1):
        if not isinstance(chapter, dict):
            raise ConfigError("each chapter must be an object")
        chapter_id = slugify(str(chapter.get("id") or chapter.get("title") or f"chapter_{ch_index}"), f"chapter_{ch_index}")
        rooms_in = as_list(chapter.get("rooms"), f"chapters[{chapter_id}].rooms")
        if not rooms_in:
            raise ConfigError(f"chapter {chapter_id} requires at least one room")
        rooms, start_room = _normalize_rooms(rooms_in, bg_dir, config_dir, asset_copies, npc_defs, items)
        quest_id = _chapter_quest(chapter, chapter_id, rooms, quests)
        rooms_path = f"res://data/rooms/{chapter_id}.json"
        room_files[chapter_id] = {
            "_note": "Generated by tfs-vn scaffold.",
            "start": start_room,
            "rooms": rooms,
        }
        intro_pages = [str(x) for x in as_list(chapter.get("intro"), f"{chapter_id}.intro")]
        outro_pages = [str(x) for x in as_list(chapter.get("outro"), f"{chapter_id}.outro")]
        intro_art = _story_card_art(chapter, "intro_art", chapter_id, rooms, len(intro_pages), avoid=[])
        outro_art = _story_card_art(chapter, "outro_art", chapter_id, rooms, len(outro_pages), avoid=intro_art)
        chapters_out.append(
            {
                "id": chapter_id,
                "title": str(chapter.get("title") or titleize_slug(chapter_id)),
                "pov": str(chapter.get("pov") or "protagonist"),
                "pov_name": str(chapter.get("pov_name") or "Protagonist"),
                "pov_desc": str(chapter.get("pov_desc") or ""),
                "rooms": rooms_path,
                "quest": quest_id,
                "intro": intro_pages,
                "intro_art": intro_art,
                "outro": outro_pages,
                "outro_art": outro_art,
            }
        )

    if cover:
        asset_copies.append((cover, Path("assets/ui/cover.png")))
    if audio_dir and audio_dir.exists():
        for src in sorted(audio_dir.glob("*.ogg")):
            asset_copies.append((src, Path("assets/audio/music") / src.name))

    return {
        "title": title,
        "subtitle": subtitle,
        "game_title": game_title,
        "description": str(config.get("description") or f"{game_title} built with TFS Visual Novel Tools."),
        "dedication": str(config.get("dedication") or ""),
        "accent": accent,
        "accent_dim": _dim_hex(accent),
        "bundle_id": str(config.get("bundle_id") or f"com.example.{slugify(title)}"),
        "binary_name": slugify(str(config.get("binary_name") or title), "game"),
        "chapters": chapters_out,
        "room_files": room_files,
        "npcs": npc_defs,
        "items": items,
        "shops": shops,
        "quests": quests,
        "cyberspace": as_object(config.get("cyberspace"), "cyberspace") or {"databases": []},
        "pax": as_object(config.get("pax"), "pax"),
        "asset_copies": asset_copies,
    }


def _normalize_rooms(
    rooms_in: list[Any],
    bg_dir: Path | None,
    config_dir: Path,
    asset_copies: list[tuple[Path, Path]],
    npc_defs: dict[str, Any],
    items: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    raw_rooms: list[dict[str, Any]] = []
    id_map: dict[str, str] = {}
    for index, room in enumerate(rooms_in, start=1):
        if not isinstance(room, dict):
            raise ConfigError("each room must be an object")
        rid = slugify(str(room.get("id") or room.get("name") or f"room_{index}"), f"room_{index}")
        raw_rooms.append(room)
        id_map[str(room.get("id") or rid)] = rid
        if room.get("name"):
            id_map[str(room["name"])] = rid

    any_exits = any(bool(as_object(room.get("exits"), "room.exits")) for room in raw_rooms)
    rooms: dict[str, Any] = {}
    for index, room in enumerate(raw_rooms):
        rid = id_map[str(room.get("id") or room.get("name") or f"room_{index + 1}")]
        out: dict[str, Any] = {
            "name": str(room.get("name") or titleize_slug(rid)),
            "desc": str(room.get("desc") or room.get("description") or titleize_slug(rid)),
            "exits": _normalize_exits(as_object(room.get("exits"), f"{rid}.exits"), id_map),
        }
        if not any_exits:
            if index > 0:
                out["exits"]["west"] = id_map[str(raw_rooms[index - 1].get("id") or raw_rooms[index - 1].get("name") or f"room_{index}")]
            if index < len(raw_rooms) - 1:
                out["exits"]["east"] = id_map[str(raw_rooms[index + 1].get("id") or raw_rooms[index + 1].get("name") or f"room_{index + 2}")]
        bg_id, bg_src = _room_background(room, rid, bg_dir, config_dir)
        if bg_id:
            out["bg"] = bg_id
        if bg_src:
            asset_copies.append((bg_src, Path("assets/backgrounds_hd") / f"{bg_id}.png"))
        for key in ("shop", "net", "matrix", "music", "on_enter_flag", "requires_flag", "locked_text"):
            if key in room:
                out[key] = room[key]
        pickups = _normalize_pickups(as_list(room.get("pickups"), f"{rid}.pickups"), items)
        if pickups:
            out["pickups"] = pickups
        npcs = _normalize_room_npcs(as_list(room.get("npcs"), f"{rid}.npcs"), npc_defs)
        if npcs:
            out["npcs"] = npcs
        rooms[rid] = out
    return rooms, next(iter(rooms))


def _story_card_art(
    chapter: dict[str, Any],
    key: str,
    chapter_id: str,
    rooms: dict[str, Any],
    pages: int,
    avoid: list[str],
) -> list[str]:
    """One plate per intro/outro story card, as res:// paths the engine loads.

    An explicit ``intro_art`` / ``outro_art`` (or chapter-wide ``art``) in the
    config wins: a plate id or a list of them, one per card. Otherwise the cards
    borrow plates from the chapter's own rooms, so a story card is never a bare
    text panel once the chapter has art. The pick is random but seeded on the
    chapter id, so re-scaffolding the same config never reshuffles the art, and
    ``avoid`` keeps the outro off the intro's plates while the chapter has
    enough to go round. The chosen plates are shown in room order.
    """
    if pages <= 0:
        return []
    explicit = chapter.get(key, chapter.get("art"))
    if explicit:
        chosen = [slugify(str(x), "plate") for x in (explicit if isinstance(explicit, list) else [explicit])]
    else:
        plates = list(dict.fromkeys(str(room["bg"]) for room in rooms.values() if room.get("bg")))
        if not plates:
            return []
        taken = {Path(path).stem for path in avoid}
        fresh = [plate for plate in plates if plate not in taken]
        pool = fresh if len(fresh) >= min(pages, len(plates)) else plates
        rng = random.Random(f"{chapter_id}:{key}")
        chosen = sorted(rng.sample(pool, min(pages, len(pool))), key=plates.index)
    # Fewer plates than cards: the last plate holds for the remaining cards,
    # which is also what the engine does with a short list.
    chosen += [chosen[-1]] * (pages - len(chosen))
    return [f"res://assets/backgrounds_hd/{plate}.png" for plate in chosen[:pages]]


def _normalize_exits(exits: dict[str, Any], id_map: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for direction, dest in exits.items():
        d = str(direction).lower().strip()
        if d not in DIRECTIONS:
            raise ConfigError(f"unknown exit direction '{direction}'")
        result[d] = id_map.get(str(dest), slugify(str(dest), "room"))
    return result


def _room_background(
    room: dict[str, Any],
    rid: str,
    bg_dir: Path | None,
    config_dir: Path,
) -> tuple[str, Path | None]:
    source_value = room.get("plate") or room.get("image") or room.get("bg_file")
    explicit_bg = str(room.get("bg") or "").strip()
    if source_value:
        src = resolve_path(bg_dir or config_dir, source_value)
        if src is None or not src.exists():
            raise ConfigError(f"background image not found for room {rid}: {source_value}")
        return slugify(explicit_bg or src.stem, rid), src
    if explicit_bg:
        src = None
        if bg_dir:
            candidate = bg_dir / f"{explicit_bg}.png"
            if candidate.exists():
                src = candidate.resolve()
        return slugify(explicit_bg, rid), src
    return "", None


def _normalize_pickups(pickups: list[Any], items: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for pickup in pickups:
        if isinstance(pickup, str):
            item_id = slugify(pickup)
            label = f"Take {titleize_slug(item_id)}"
        elif isinstance(pickup, dict):
            item_id = slugify(str(pickup.get("item") or pickup.get("id") or pickup.get("name") or "item"))
            label = str(pickup.get("label") or f"Take {titleize_slug(item_id)}")
        else:
            raise ConfigError("pickups must be strings or objects")
        items.setdefault(
            item_id,
            {
                "name": titleize_slug(item_id),
                "type": "misc",
                "key": True,
                "price": 0,
                "desc": titleize_slug(item_id),
            },
        )
        result.append({"item": item_id, "label": label})
    return result


def _normalize_room_npcs(npcs: list[Any], npc_defs: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for npc in npcs:
        if isinstance(npc, str):
            npc_id = slugify(npc)
            npc_defs.setdefault(npc_id, _default_npc(npc_id))
        elif isinstance(npc, dict):
            npc_id = slugify(str(npc.get("id") or npc.get("name") or "npc"))
            npc_defs[npc_id] = _normalize_npc(npc_id, npc)
        else:
            raise ConfigError("npcs must be strings or objects")
        result.append(npc_id)
    return result


def _initial_npcs(config: dict[str, Any]) -> dict[str, Any]:
    raw = config.get("npcs") or {}
    if isinstance(raw, list):
        entries = raw
    elif isinstance(raw, dict):
        entries = [{"id": key, **value} if isinstance(value, dict) else {"id": key, "text": str(value)} for key, value in raw.items()]
    else:
        raise ConfigError("npcs must be an object or list")
    return {slugify(str(e.get("id") or e.get("name") or "npc")): _normalize_npc(slugify(str(e.get("id") or e.get("name") or "npc")), e) for e in entries}


def _normalize_npc(npc_id: str, data: dict[str, Any]) -> dict[str, Any]:
    if "nodes" in data:
        nodes = as_object(data["nodes"], f"npc {npc_id}.nodes")
        return {
            "id": npc_id,
            "name": str(data.get("name") or titleize_slug(npc_id)),
            "start": str(data.get("start") or next(iter(nodes), "hello")),
            "nodes": nodes,
        }
    node = {
        "text": str(data.get("text") or f"{titleize_slug(npc_id)} has nothing else to say."),
        "options": [],
    }
    if data.get("set_flag"):
        node["set_flag"] = str(data["set_flag"])
    return {"id": npc_id, "name": str(data.get("name") or titleize_slug(npc_id)), "start": "hello", "nodes": {"hello": node}}


def _default_npc(npc_id: str) -> dict[str, Any]:
    return _normalize_npc(npc_id, {"id": npc_id})


def _chapter_quest(
    chapter: dict[str, Any],
    chapter_id: str,
    rooms: dict[str, Any],
    quests: dict[str, Any],
) -> str:
    quest = chapter.get("quest")
    if isinstance(quest, dict):
        qid = slugify(str(quest.get("id") or f"q_{chapter_id}"), f"q_{chapter_id}")
        quests[qid] = {k: v for k, v in quest.items() if k != "id"}
        return qid
    if isinstance(quest, str) and quest:
        qid = slugify(quest, f"q_{chapter_id}")
        quests.setdefault(qid, _default_quest(chapter_id, rooms))
        return qid
    qid = f"q_{chapter_id}"
    quests.setdefault(qid, _default_quest(chapter_id, rooms))
    return qid


def _default_quest(chapter_id: str, rooms: dict[str, Any]) -> dict[str, Any]:
    last_id = next(reversed(rooms))
    flag = str(rooms[last_id].get("on_enter_flag") or f"visited_{last_id}")
    rooms[last_id].setdefault("on_enter_flag", flag)
    return {
        "name": f"Explore {titleize_slug(chapter_id)}",
        "desc": "Reach the end of the chapter.",
        "steps": [{"text": f"Reach {rooms[last_id]['name']}.", "flag": flag}],
    }


def _initial_collection(value: Any, key: str) -> dict[str, Any]:
    raw = as_object(value, key)
    if key in raw and isinstance(raw[key], dict):
        raw = raw[key]
    return {slugify(str(k)): v for k, v in raw.items()}


def _write_generated_data(out_dir: Path, generated: dict[str, Any]) -> None:
    data_dir = out_dir / "data"
    write_json(
        data_dir / "chapters.json",
        {
            "_note": "Generated by tfs-vn scaffold.",
            "game": generated["game_title"],
            "dedication": generated["dedication"],
            "chapters": generated["chapters"],
        },
    )
    for chapter_id, room_file in generated["room_files"].items():
        write_json(data_dir / "rooms" / f"{chapter_id}.json", room_file)
    for npc_id, npc in generated["npcs"].items():
        write_json(data_dir / "npcs" / f"{npc_id}.json", npc)
    write_json(data_dir / "quests.json", {"_note": "Generated by tfs-vn scaffold.", "quests": generated["quests"]})
    write_json(data_dir / "items.json", {"_note": "Generated by tfs-vn scaffold.", "items": generated["items"]})
    write_json(data_dir / "shops.json", {"_note": "Generated by tfs-vn scaffold.", "shops": generated["shops"]})
    write_json(data_dir / "cyberspace" / "databases.json", generated["cyberspace"])
    pax = generated["pax"]
    write_json(data_dir / "pax" / "news.json", pax.get("news") or {"news": []})
    write_json(data_dir / "pax" / "bbs.json", pax.get("bbs") or {"boards": []})


def _copy_assets(out_dir: Path, generated: dict[str, Any]) -> None:
    for src, rel_dst in generated["asset_copies"]:
        src = Path(src)
        dst = out_dir / rel_dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not src.exists():
            raise ConfigError(f"asset not found: {src}")
        if rel_dst.suffix.lower() == ".png" and src.suffix.lower() != ".png":
            _convert_to_png(src, dst)
        else:
            shutil.copy2(src, dst)


def _convert_to_png(src: Path, dst: Path) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ConfigError(f"{src} must be PNG unless Pillow is installed") from exc
    with Image.open(src) as image:
        image.save(dst, "PNG")


def _rebrand_project(out_dir: Path, generated: dict[str, Any]) -> None:
    project_path = out_dir / "project.godot"
    project_text = project_path.read_text(encoding="utf-8")
    project_text = _replace_setting(project_text, "config/name", godot_string(generated["game_title"]))
    project_text = _replace_setting(project_text, "config/description", godot_string(generated["description"]))
    project_path.write_text(project_text, encoding="utf-8")

    export_path = out_dir / "export_presets.cfg"
    if export_path.exists():
        binary = generated["binary_name"]
        text = export_path.read_text(encoding="utf-8")
        text = _replace_setting(text, "export_path", godot_string(f"build/linux/{binary}.x86_64"), occurrence=1)
        text = _replace_setting(text, "export_path", godot_string(f"build/windows/{binary}.exe"), occurrence=2)
        text = _replace_setting(text, "export_path", godot_string(f"build/macos/{binary}.zip"), occurrence=3)
        text = _replace_setting(text, "application/bundle_identifier", godot_string(generated["bundle_id"]))
        export_path.write_text(text, encoding="utf-8")

    theme_path = out_dir / "src/ui/UITheme.gd"
    theme_text = theme_path.read_text(encoding="utf-8")
    theme_text = _replace_color_const(theme_text, "ACCENT", generated["accent"].lstrip("#"))
    theme_text = _replace_color_const(theme_text, "ACCENT_DIM", generated["accent_dim"].lstrip("#"))
    theme_path.write_text(theme_text, encoding="utf-8")


def _replace_setting(text: str, key: str, value: str, occurrence: int = 1) -> str:
    lines = text.splitlines()
    seen = 0
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            seen += 1
            if seen == occurrence:
                lines[i] = f"{key}={value}"
                break
    return "\n".join(lines) + "\n"


def _replace_color_const(text: str, name: str, hex_value: str) -> str:
    lines = text.splitlines()
    prefix = f"const {name} := Color("
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            comment = ""
            if "#" in line:
                comment = "  #" + line.split("#", 1)[1]
            lines[i] = f'const {name} := Color("{hex_value}"){comment}'
            break
    return "\n".join(lines) + "\n"


def _join_title(title: str, subtitle: str) -> str:
    return f"{title} \u2014 {subtitle}" if subtitle else title


def _normalize_hex(value: str) -> str:
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    if len(value) != 7 or any(c not in "0123456789abcdefABCDEF" for c in value[1:]):
        raise ConfigError(f"accent must be a hex color like #37d2c3, got {value}")
    return value.lower()


def _dim_hex(value: str) -> str:
    value = _normalize_hex(value).lstrip("#")
    parts = [int(value[i : i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{max(0, int(p * 0.52)):02x}" for p in parts)
