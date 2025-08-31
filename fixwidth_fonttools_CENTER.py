#!/usr/bin/env python3
import argparse
from pathlib import Path
from fontTools.ttLib import TTFont

def process_font(font_path: Path, fixed_width: int, suffix: str):
    font = TTFont(str(font_path))

    # Robustly read the English family name
    try:
        base_family = font['name'].getName(1, 3, 1, 0x409).toUnicode()
    except Exception:
        base_family = "Font"

    new_family = base_family + suffix
    new_fullname = new_family
    new_fontname = new_family.replace(" ", "")

    # Center each glyph within the fixed width
    hmtx = font["hmtx"]
    glyf = font.get("glyf", None)

    for glyph_name in font.getGlyphOrder():
        if glyf and glyph_name in glyf and hasattr(glyf[glyph_name], "xMin"):
            g = glyf[glyph_name]
            drawn = (g.xMax if g.xMax is not None else 0) - (g.xMin if g.xMin is not None else 0)
            if drawn < 0:
                drawn = 0
            new_left = int(round((fixed_width - drawn) / 2))
            if new_left < 0:
                new_left = 0
            hmtx[glyph_name] = (fixed_width, new_left)
        else:
            w, lsb = hmtx[glyph_name]
            drawn = w
            new_left = int(round((fixed_width - drawn) / 2))
            if new_left < 0:
                new_left = 0
            hmtx[glyph_name] = (fixed_width, new_left)

    # Update naming (Name table)
    name_table = font["name"]
    name_table.setName(new_family, 1, 3, 1, 0x409)   # Font Family name
    name_table.setName(new_fullname, 4, 3, 1, 0x409)  # Full font name
    name_table.setName(new_fontname, 6, 3, 1, 0x409)  # PostScript name

    # Save to a new filename based on the font name with "-Mono" before the extension
    out_path = font_path.with_name(f"{new_fontname}-Mono{font_path.suffix}")
    font.save(str(out_path))
    font.close()

def main():
    parser = argparse.ArgumentParser(description="Set a fixed advance width for all glyphs and center glyphs in the cell for all fonts in out/ttf.")
    parser.add_argument("--width", required=True, type=int, help="Fixed width in font units")
    parser.add_argument("--mono-suffix", dest="mono_suffix", default=" Mono",
                        help="Suffix to append to the font family name for monospace variant (e.g., ' Mono')")
    args = parser.parse_args()

    fixed_width = args.width
    suffix = args.mono_suffix
    if not suffix.startswith(" "):
        suffix = " " + suffix

    def process_dir(dir_path: Path, fixed_width: int, suffix: str):
        if not dir_path.exists() or not dir_path.is_dir():
            raise SystemExit(f"Directory not found: {dir_path}")

        for file_path in sorted(dir_path.iterdir()):
            print(file_path)
            if file_path.is_file() and file_path.suffix.lower() in {".ttf", ".otf"}:
                print(f"Processing {file_path}")
                try:
                    process_font(file_path, fixed_width, suffix)
                except Exception as e:
                    print(f"Failed to process {file_path}: {e}")

    process_dir(Path("out/ttf"), fixed_width, suffix)
    process_dir(Path("out/otf"), fixed_width, suffix)

if __name__ == "__main__":
    main()
