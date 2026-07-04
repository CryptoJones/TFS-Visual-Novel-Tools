#!/usr/bin/env python3
"""
build_artbook.py -- Reusable art-book PDF generator for The Flatline Sessions II & III.

Reads each repo's docs/art-review-index.md (ordered plate list) plus the
re-rendered story-plate manifests (scratchpad JSON) and emits a landscape,
16:9, dark-themed "art book" PDF:

  Page 1  = title page (album cover + title/subtitle)
  Then per plate, in index order, TWO pages:
    - image page (plate PNG, as large as possible, centered on dark)
    - info page  (plate number, type/room, story caption, full render prompt)

For any plate whose PNG basename matches a manifest entry, the manifest's
corrected `prompt` and `story_desc` (and `room`) are used instead of the index
text. Missing plate images are skipped and reported.

Images are re-encoded to JPEG (quality 85) for compactness before embedding;
the final PDF is then compressed with Ghostscript to stay well under 100 MB.

Usage:  python3 build_artbook.py            # builds both books
        python3 build_artbook.py II         # just II
        python3 build_artbook.py III        # just III
"""

import os
import re
import sys
import json
import html
import shutil
import tempfile
import subprocess

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import Paragraph, Frame

# --------------------------------------------------------------------------
# Paths / config
# --------------------------------------------------------------------------
SCRATCH = os.path.dirname(os.path.abspath(__file__))

BOOKS = {
    "II": {
        "repo": "/home/hermes/Source/repos/TheFlatlineSessionsII",
        "manifests": [
            os.path.join(SCRATCH, "manifest_II_ch01-05.json"),
            os.path.join(SCRATCH, "manifest_II_ch06-09.json"),
        ],
        "album": "/home/hermes/Source/repos/TheFlatlineSessionsII/docs/album_art/the_flatline_sessions_ii_count_binary.png",
        "title": "The Art of The Flatline Sessions II",
        "subtitle": "Count Binary",
        "out": "/home/hermes/Source/repos/TheFlatlineSessionsII/docs/The_Art_of_The_Flatline_Sessions_II.pdf",
        "accent": "#4fd6d6",   # teal / cyan
        "dedication": "Dedicated to William Gibson and all other Science Fiction authors; past, present, and future.",
        "cover_image": os.path.join(SCRATCH, "renders", "title_boxmaker_3.png"),
        "title_screen": os.path.join(SCRATCH, "renders", "title_cowboy_2.png"),
    },
    "III": {
        "repo": "/home/hermes/Source/repos/TheFlatlineSessionsIII",
        "manifests": [
            os.path.join(SCRATCH, "manifest_III_ch01-06.json"),
            os.path.join(SCRATCH, "manifest_III_ch07-12.json"),
        ],
        "album": "/home/hermes/Source/repos/TheFlatlineSessionsIII/docs/album_art/the_flatline_sessions_iii_mona_lisa_underdrive.png",
        "title": "The Art of The Flatline Sessions III",
        "subtitle": "Mona Lisa Overdrive",
        "out": "/home/hermes/Source/repos/TheFlatlineSessionsIII/docs/The_Art_of_The_Flatline_Sessions_III.pdf",
        "accent": "#c58af0",   # violet / magenta
    },
}

# 16:9 widescreen page (13.333in x 7.5in) in points
PAGE_W, PAGE_H = 960.0, 540.0
BG = HexColor("#0c0e13")          # near-black dark page
INK = HexColor("#e8e9ee")         # primary light text
MUTED = HexColor("#9aa0ad")       # secondary text
FAINT = HexColor("#6b7280")       # tertiary
MARGIN = 30.0                     # image page margin
JPEG_QUALITY = 85
MAX_EDGE = 1600                   # cap embedded image longest edge

# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------
def parse_index(md_path):
    """Return ordered list of dicts: {plate, type, source, text}."""
    rows = []
    with open(md_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4:
                continue
            plate = cells[0]
            if not re.match(r"^P\d+$", plate):   # skip header / separator rows
                continue
            source = cells[2].strip().strip("`").strip()
            rows.append({
                "plate": plate,
                "type": cells[1],
                "source": source,
                "text": cells[3],
            })
    return rows


def load_manifests(paths):
    """Merge manifest JSON files into a lookup keyed by PNG basename."""
    lookup = {}
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for entry in json.load(fh):
                png = entry.get("png")
                if png:
                    lookup[os.path.basename(png)] = entry
    return lookup


# --------------------------------------------------------------------------
# Image helper
# --------------------------------------------------------------------------
def to_jpeg(src_png, tmpdir):
    """Re-encode a PNG to a compact JPEG; return temp path (or None on error)."""
    try:
        im = Image.open(src_png)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > MAX_EDGE:
            scale = MAX_EDGE / float(max(w, h))
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        base = os.path.splitext(os.path.basename(src_png))[0]
        out = os.path.join(tmpdir, base + ".jpg")
        im.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
        return out, im.size
    except Exception as exc:                     # noqa: BLE001
        print("    ! image error %s: %s" % (src_png, exc))
        return None, None


def draw_fitted(c, img_path, size, box_x, box_y, box_w, box_h):
    """Draw image scaled to fit box, centered, preserving aspect."""
    iw, ih = size
    scale = min(box_w / iw, box_h / ih)
    dw, dh = iw * scale, ih * scale
    x = box_x + (box_w - dw) / 2.0
    y = box_y + (box_h - dh) / 2.0
    c.drawImage(img_path, x, y, dw, dh, preserveAspectRatio=True, mask="auto")


def fill_page(c):
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)


# --------------------------------------------------------------------------
# Page builders
# --------------------------------------------------------------------------
def title_page(c, tmpdir, book):
    fill_page(c)
    # full-bleed cover art (Box-Maker); fall back to the album cover
    cover = book["cover_image"] if book.get("cover_image") and os.path.exists(book["cover_image"]) else book["album"]
    if os.path.exists(cover):
        jpg, size = to_jpeg(cover, tmpdir)
        if jpg:
            draw_fitted(c, jpg, size, 0, 0, PAGE_W, PAGE_H)
    # dark scrim across the bottom for title legibility
    c.saveState()
    c.setFillColor(BG)
    c.setFillAlpha(0.62)
    c.rect(0, 0, PAGE_W, 138, stroke=0, fill=1)
    c.restoreState()
    # title
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 33)
    c.drawCentredString(PAGE_W / 2, 84, book["title"])
    # accent rule
    c.setStrokeColor(HexColor(book["accent"]))
    c.setLineWidth(1)
    c.line(PAGE_W / 2 - 120, 70, PAGE_W / 2 + 120, 70)
    # subtitle
    c.setFillColor(HexColor(book["accent"]))
    c.setFont("Helvetica-Oblique", 20)
    c.drawCentredString(PAGE_W / 2, 44, book["subtitle"])
    c.showPage()


def image_page(c, jpg, size):
    fill_page(c)
    draw_fitted(c, jpg, size, MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN)
    c.showPage()


def info_page(c, plate, type_str, room, caption, prompt, accent):
    fill_page(c)
    accent_col = HexColor(accent)

    # accent side bar
    c.setFillColor(accent_col)
    c.rect(0, 0, 8, PAGE_H, stroke=0, fill=1)

    # big plate number
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(48, PAGE_H - 74, "Plate %s" % plate)
    # accent underline
    c.setStrokeColor(accent_col)
    c.setLineWidth(2)
    c.line(50, PAGE_H - 88, 300, PAGE_H - 88)

    styles_label = ParagraphStyle(
        "label", fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=accent_col, spaceAfter=2, spaceBefore=8)
    styles_val = ParagraphStyle(
        "val", fontName="Helvetica", fontSize=11.5, leading=15.5,
        textColor=INK, alignment=TA_LEFT)
    styles_promptlbl = ParagraphStyle(
        "plabel", fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=accent_col, spaceAfter=3, spaceBefore=12)
    styles_prompt = ParagraphStyle(
        "prompt", fontName="Helvetica", fontSize=9.6, leading=13.2,
        textColor=MUTED, alignment=TA_LEFT)

    def esc(s):
        return html.escape(s, quote=False)

    flow = []
    flow.append(Paragraph("Type", styles_label))
    flow.append(Paragraph(esc(type_str), styles_val))
    if room:
        flow.append(Paragraph("Room", styles_label))
        flow.append(Paragraph(esc(room), styles_val))
    if caption:
        flow.append(Paragraph("Story caption", styles_label))
        flow.append(Paragraph(esc(caption), styles_val))
    flow.append(Paragraph("Render prompt", styles_promptlbl))
    flow.append(Paragraph(esc(prompt), styles_prompt))

    frame = Frame(48, 36, PAGE_W - 48 - 44, PAGE_H - 74 - 48,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                  showBoundary=0)
    frame.addFromList(flow, c)
    c.showPage()


def dedication_page(c, text, accent):
    """Closing dedication page: accent rule above, centered italic dedication below."""
    fill_page(c)
    c.setStrokeColor(HexColor(accent))
    c.setLineWidth(1)
    c.line(PAGE_W / 2 - 60, PAGE_H / 2 + 46, PAGE_W / 2 + 60, PAGE_H / 2 + 46)
    style = ParagraphStyle("ded", fontName="Helvetica-Oblique", fontSize=21, leading=31,
                           textColor=INK, alignment=1)  # 1 = TA_CENTER
    para = Paragraph(html.escape(text, quote=False), style)
    frame = Frame(PAGE_W / 2 - 330, PAGE_H / 2 - 80, 660, 110,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0)
    frame.addFromList([para], c)
    c.showPage()


# --------------------------------------------------------------------------
# Build one book
# --------------------------------------------------------------------------
def build_book(key, run_gs=True):
    book = BOOKS[key]
    repo = book["repo"]
    index_md = os.path.join(repo, "docs", "art-review-index.md")
    rows = parse_index(index_md)
    manifests = load_manifests(book["manifests"])

    tmpdir = tempfile.mkdtemp(prefix="artbook_%s_" % key, dir=SCRATCH)
    raw_pdf = os.path.join(tmpdir, "raw_%s.pdf" % key)

    c = canvas.Canvas(raw_pdf, pagesize=(PAGE_W, PAGE_H))
    c.setTitle(book["title"])

    title_page(c, tmpdir, book)

    # page 2: the game title screen (console-cowboy), full image
    ts = book.get("title_screen")
    if ts and os.path.exists(ts):
        tjpg, tsize = to_jpeg(ts, tmpdir)
        if tjpg:
            image_page(c, tjpg, tsize)

    skipped = []
    used = 0
    for row in rows:
        src = os.path.join(repo, row["source"])
        png_base = os.path.basename(row["source"])
        if not os.path.exists(src):
            skipped.append((row["plate"], row["source"]))
            continue
        jpg, size = to_jpeg(src, tmpdir)
        if not jpg:
            skipped.append((row["plate"], row["source"]))
            continue

        m = manifests.get(png_base)
        if m:
            prompt = m.get("prompt") or row["text"]
            caption = m.get("story_desc") or ""
            room = m.get("room") or ""
        else:
            prompt = row["text"]
            caption = ""
            room = ""

        image_page(c, jpg, size)
        # art-only book: per-plate info/text pages removed (CJ approved 2026-07-03)
        used += 1

    if book.get("dedication"):
        dedication_page(c, book["dedication"], book["accent"])

    c.save()

    raw_size = os.path.getsize(raw_pdf) / 1e6
    print("[%s] raw PDF: %.1f MB, plates used: %d" % (key, raw_size, used))
    if skipped:
        print("[%s] skipped (missing image): %s" %
              (key, ", ".join("%s %s" % (p, s) for p, s in skipped)))

    out = os.environ.get("ARTBOOK_OUT", book["out"])
    if run_gs:
        ok = ghostscript_compress(raw_pdf, out, target_mb=100)
        if not ok:
            shutil.copyfile(raw_pdf, out)
    else:
        shutil.copyfile(raw_pdf, out)

    final_mb = os.path.getsize(out) / 1e6
    print("[%s] wrote %s (%.1f MB)" % (key, out, final_mb))
    shutil.rmtree(tmpdir, ignore_errors=True)
    ded = 1 if book.get("dedication") else 0
    tsp = 1 if (book.get("title_screen") and os.path.exists(book["title_screen"])) else 0
    return {"out": out, "pages": used + 1 + tsp + ded, "plates": used,
            "skipped": skipped, "size_mb": final_mb}


def ghostscript_compress(src, dst, target_mb=100):
    """Compress with Ghostscript; escalate settings until under target."""
    attempts = [
        ("/ebook", 150),
        ("/ebook", 120),
        ("/screen", 100),
        ("/screen", 72),
    ]
    for preset, dpi in attempts:
        cmd = [
            "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
            "-dPDFSETTINGS=%s" % preset, "-dNOPAUSE", "-dBATCH", "-dQUIET",
            "-dDetectDuplicateImages=true",
            "-dColorImageDownsampleType=/Bicubic",
            "-dColorImageResolution=%d" % dpi,
            "-dGrayImageDownsampleType=/Bicubic",
            "-dGrayImageResolution=%d" % dpi,
            "-sOutputFile=%s" % dst, src,
        ]
        try:
            subprocess.run(cmd, check=True)
        except Exception as exc:                 # noqa: BLE001
            print("    ! ghostscript failed (%s %ddpi): %s" % (preset, dpi, exc))
            return False
        mb = os.path.getsize(dst) / 1e6
        print("    gs %s @%ddpi -> %.1f MB" % (preset, dpi, mb))
        if mb < target_mb:
            return True
    return True  # last attempt kept even if still large


# --------------------------------------------------------------------------
def main():
    which = sys.argv[1:] or ["II", "III"]
    results = {}
    for key in which:
        key = key.upper().replace("SESSIONSII", "II").replace("SESSIONSIII", "III")
        if key not in BOOKS:
            print("unknown book:", key)
            continue
        print("=" * 60)
        print("Building", key)
        print("=" * 60)
        results[key] = build_book(key)
    print("\n===== SUMMARY =====")
    for key, r in results.items():
        print("%s: %d pages, %.1f MB, %d plates, %d skipped -> %s" %
              (key, r["pages"], r["size_mb"], r["plates"], len(r["skipped"]), r["out"]))


if __name__ == "__main__":
    main()
