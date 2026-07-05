"""Config-driven PDF art-book generation."""

from __future__ import annotations

import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

from .config import ConfigError, load_json, resolve_path


PAGE_W, PAGE_H = 960.0, 540.0
MARGIN = 30.0
JPEG_QUALITY = 85
MAX_EDGE = 1600


def build_artbook_from_config(config_path: str | Path, *, compress: bool = True) -> dict[str, Any]:
    src = Path(config_path).expanduser().resolve()
    config = load_artbook_config(src)
    return build_artbook(config, compress=compress)


def load_artbook_config(config_path: str | Path) -> dict[str, Any]:
    src = Path(config_path).expanduser().resolve()
    base = src.parent
    data = load_json(src)
    title = str(data.get("title") or "").strip()
    if not title:
        raise ConfigError(f"{src}: artbook title is required")
    out = resolve_path(base, data.get("out"))
    if out is None:
        raise ConfigError(f"{src}: artbook out path is required")
    repo = resolve_path(base, data.get("repo")) if data.get("repo") else None
    index = resolve_path(base if repo is None else repo, data.get("index") or "docs/art-review-index.md")
    manifests = [resolve_path(base, p) for p in data.get("manifests", [])]
    plates = data.get("plates")
    if plates is not None and not isinstance(plates, list):
        raise ConfigError(f"{src}: plates must be a list")
    asset_dir = resolve_path(base, data.get("asset_dir")) if data.get("asset_dir") else None
    return {
        "config_path": src,
        "base": base,
        "repo": repo,
        "index": index,
        "manifests": [p for p in manifests if p is not None],
        "asset_dir": asset_dir,
        "plates": plates,
        "title": title,
        "subtitle": str(data.get("subtitle") or ""),
        "out": out,
        "accent": _normalize_hex(str(data.get("accent") or "#37d2c3")),
        "dedication": str(data.get("dedication") or ""),
        "cover_image": resolve_path(base, data.get("cover") or data.get("cover_image")),
        "title_screen": resolve_path(base, data.get("title_screen")),
        "target_mb": int(data.get("target_mb") or 100),
    }


def parse_index(md_path: str | Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = Path(md_path)
    if not path.exists():
        raise ConfigError(f"art-review index not found: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        plate = cells[0]
        if not re.match(r"^P\d+$", plate):
            continue
        rows.append(
            {
                "plate": plate,
                "type": cells[1],
                "source": cells[2].strip().strip("`").strip(),
                "text": cells[3],
            }
        )
    return rows


def load_manifests(paths: list[Path]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for path in paths:
        if path is None or not path.exists():
            raise ConfigError(f"manifest not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ConfigError(f"{path}: manifest must be a list")
        for entry in data:
            if not isinstance(entry, dict):
                continue
            png = entry.get("png")
            if png:
                lookup[Path(str(png)).name] = entry
    return lookup


def build_artbook(config: dict[str, Any], *, compress: bool = True) -> dict[str, Any]:
    try:
        from PIL import Image
        from reportlab.lib.colors import HexColor
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Frame, Paragraph
    except ImportError as exc:
        raise ConfigError("artbook generation requires Pillow and reportlab") from exc

    bg = HexColor("#0c0e13")
    ink = HexColor("#e8e9ee")
    muted = HexColor("#9aa0ad")
    accent = HexColor(config["accent"])

    def fill_page(c: Any) -> None:
        c.setFillColor(bg)
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    def to_jpeg(src_png: Path, tmpdir: Path) -> tuple[Path | None, tuple[int, int] | None]:
        try:
            im = Image.open(src_png)
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > MAX_EDGE:
                scale = MAX_EDGE / float(max(w, h))
                im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            out = tmpdir / f"{src_png.stem}.jpg"
            im.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
            return out, im.size
        except Exception as exc:  # noqa: BLE001
            print(f"    ! image error {src_png}: {exc}")
            return None, None

    def draw_fitted(c: Any, img_path: Path, size: tuple[int, int], box_x: float, box_y: float, box_w: float, box_h: float) -> None:
        iw, ih = size
        scale = min(box_w / iw, box_h / ih)
        dw, dh = iw * scale, ih * scale
        x = box_x + (box_w - dw) / 2.0
        y = box_y + (box_h - dh) / 2.0
        c.drawImage(str(img_path), x, y, dw, dh, preserveAspectRatio=True, mask="auto")

    def image_page(c: Any, jpg: Path, size: tuple[int, int]) -> None:
        fill_page(c)
        draw_fitted(c, jpg, size, MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN)
        c.showPage()

    def title_page(c: Any, tmpdir: Path) -> None:
        fill_page(c)
        cover = config.get("cover_image")
        if cover and Path(cover).exists():
            jpg, size = to_jpeg(Path(cover), tmpdir)
            if jpg and size:
                draw_fitted(c, jpg, size, 0, 0, PAGE_W, PAGE_H)
        c.saveState()
        c.setFillColor(bg)
        c.setFillAlpha(0.62)
        c.rect(0, 0, PAGE_W, 138, stroke=0, fill=1)
        c.restoreState()
        c.setFillColor(ink)
        c.setFont("Helvetica-Bold", 33)
        c.drawCentredString(PAGE_W / 2, 84, config["title"])
        c.setStrokeColor(accent)
        c.setLineWidth(1)
        c.line(PAGE_W / 2 - 120, 70, PAGE_W / 2 + 120, 70)
        c.setFillColor(accent)
        c.setFont("Helvetica-Oblique", 20)
        c.drawCentredString(PAGE_W / 2, 44, config["subtitle"])
        c.showPage()

    def info_page(c: Any, plate: str, type_str: str, room: str, caption: str, prompt: str) -> None:
        fill_page(c)
        c.setFillColor(accent)
        c.rect(0, 0, 8, PAGE_H, stroke=0, fill=1)
        c.setFillColor(ink)
        c.setFont("Helvetica-Bold", 34)
        c.drawString(48, PAGE_H - 74, f"Plate {plate}")
        c.setStrokeColor(accent)
        c.setLineWidth(2)
        c.line(50, PAGE_H - 88, 300, PAGE_H - 88)
        styles_label = ParagraphStyle(
            "label",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=accent,
            spaceAfter=2,
            spaceBefore=8,
        )
        styles_val = ParagraphStyle(
            "val",
            fontName="Helvetica",
            fontSize=11.5,
            leading=15.5,
            textColor=ink,
            alignment=TA_LEFT,
        )
        styles_prompt = ParagraphStyle(
            "prompt",
            fontName="Helvetica",
            fontSize=9.6,
            leading=13.2,
            textColor=muted,
            alignment=TA_LEFT,
        )
        flow = [Paragraph("Type", styles_label), Paragraph(_esc(type_str), styles_val)]
        if room:
            flow.extend([Paragraph("Room", styles_label), Paragraph(_esc(room), styles_val)])
        if caption:
            flow.extend([Paragraph("Story caption", styles_label), Paragraph(_esc(caption), styles_val)])
        flow.extend([Paragraph("Render prompt", styles_label), Paragraph(_esc(prompt), styles_prompt)])
        frame = Frame(48, 36, PAGE_W - 92, PAGE_H - 122, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        frame.addFromList(flow, c)
        c.showPage()

    def dedication_page(c: Any) -> None:
        fill_page(c)
        c.setStrokeColor(accent)
        c.setLineWidth(1)
        c.line(PAGE_W / 2 - 60, PAGE_H / 2 + 46, PAGE_W / 2 + 60, PAGE_H / 2 + 46)
        style = ParagraphStyle("ded", fontName="Helvetica-Oblique", fontSize=21, leading=31, textColor=ink, alignment=1)
        para = Paragraph(_esc(config["dedication"]), style)
        frame = Frame(PAGE_W / 2 - 330, PAGE_H / 2 - 80, 660, 110, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        frame.addFromList([para], c)
        c.showPage()

    tmpdir = Path(tempfile.mkdtemp(prefix="artbook_", dir=str(config["base"])))
    raw_pdf = tmpdir / "raw.pdf"
    out = Path(config["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    skipped: list[tuple[str, str]] = []
    used = 0
    pages = 0
    try:
        c = canvas.Canvas(str(raw_pdf), pagesize=(PAGE_W, PAGE_H))
        c.setTitle(config["title"])
        title_page(c, tmpdir)
        pages += 1
        title_screen = config.get("title_screen")
        if title_screen and Path(title_screen).exists():
            jpg, size = to_jpeg(Path(title_screen), tmpdir)
            if jpg and size:
                image_page(c, jpg, size)
                pages += 1

        manifests = load_manifests(config.get("manifests", []))
        for row in _plate_rows(config):
            src = _plate_source(config, row)
            plate = str(row.get("plate") or f"{used + 1:03d}")
            if src is None or not src.exists():
                skipped.append((plate, str(row.get("source") or "")))
                continue
            jpg, size = to_jpeg(src, tmpdir)
            if not jpg or not size:
                skipped.append((plate, str(src)))
                continue
            manifest = manifests.get(src.name)
            prompt = str((manifest or {}).get("prompt") or row.get("prompt") or row.get("text") or "")
            caption = str((manifest or {}).get("story_desc") or row.get("caption") or "")
            room = str((manifest or {}).get("room") or row.get("room") or "")
            image_page(c, jpg, size)
            pages += 1
            if row.get("info_page"):
                info_page(c, plate, str(row.get("type") or ""), room, caption, prompt)
                pages += 1
            used += 1
        if config.get("dedication"):
            dedication_page(c)
            pages += 1
        c.save()
        if compress:
            ok = ghostscript_compress(raw_pdf, out, target_mb=config["target_mb"])
            if not ok:
                shutil.copyfile(raw_pdf, out)
        else:
            shutil.copyfile(raw_pdf, out)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    if skipped:
        print("skipped missing images: " + ", ".join(f"{p} {s}" for p, s in skipped))
    return {
        "out": str(out),
        "pages": pages,
        "plates": used,
        "skipped": skipped,
        "size_mb": out.stat().st_size / 1e6 if out.exists() else 0.0,
    }


def ghostscript_compress(src: Path, dst: Path, target_mb: int = 100) -> bool:
    gs = shutil.which("gs")
    if gs is None:
        return False
    attempts = [
        ("/ebook", 150),
        ("/ebook", 120),
        ("/screen", 100),
        ("/screen", 72),
    ]
    for preset, dpi in attempts:
        cmd = [
            gs,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.5",
            f"-dPDFSETTINGS={preset}",
            "-dNOPAUSE",
            "-dBATCH",
            "-dQUIET",
            "-dDetectDuplicateImages=true",
            "-dColorImageDownsampleType=/Bicubic",
            f"-dColorImageResolution={dpi}",
            "-dGrayImageDownsampleType=/Bicubic",
            f"-dGrayImageResolution={dpi}",
            f"-sOutputFile={dst}",
            str(src),
        ]
        try:
            subprocess.run(cmd, check=True)
        except Exception as exc:  # noqa: BLE001
            print(f"    ! ghostscript failed ({preset} {dpi}dpi): {exc}")
            return False
        mb = dst.stat().st_size / 1e6
        print(f"    gs {preset} @{dpi}dpi -> {mb:.1f} MB")
        if mb < target_mb:
            return True
    return True


def _plate_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    if config.get("plates") is not None:
        return [r for r in config["plates"] if isinstance(r, dict)]
    return parse_index(config["index"])


def _plate_source(config: dict[str, Any], row: dict[str, Any]) -> Path | None:
    source = row.get("source")
    if not source:
        return None
    p = Path(str(source)).expanduser()
    if p.is_absolute():
        return p
    if config.get("plates") is not None and config.get("asset_dir"):
        return Path(config["asset_dir"]) / p
    if config.get("repo"):
        return Path(config["repo"]) / p
    return Path(config["base"]) / p


def _normalize_hex(value: str) -> str:
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    if len(value) != 7 or any(c not in "0123456789abcdefABCDEF" for c in value[1:]):
        raise ConfigError(f"accent must be a hex color like #37d2c3, got {value}")
    return value.lower()


def _esc(value: str) -> str:
    return html.escape(value, quote=False)
