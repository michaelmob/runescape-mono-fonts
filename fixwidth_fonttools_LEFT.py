#!/usr/bin/env python3
import argparse
import sys
from fontTools.ttLib import TTFont

def main():
    parser = argparse.ArgumentParser(
        description="Left-align each glyph within a fixed width (no stretching)."
    )
    parser.add_argument("--src", required=True, help="Source font file")
    parser.add_argument("--dst", required=True, help="Output font file")
    parser.add_argument("--width", required=True, type=int, help="Fixed width in font units")
    parser.add_argument("--mono-suffix", dest="mono_suffix", default=" Mono",
                        help="Suffix to append to the font family name for monospace variant (e.g., ' Mono')")
    args = parser.parse_args()

    src = args.src
    dst = args.dst
    fixed_width = args.width
    suffix = args.mono_suffix
    if not suffix.startswith(" "):
        suffix = " " + suffix

    font = TTFont(src)

    # Robustly read the English family name
    try:
        base_family = font['name'].getName(1, 3, 1, 0x409).toUnicode()
    except Exception:
        base_family = "Font"

    new_family = base_family + suffix
    new_fullname = new_family
    new_fontname = new_family.replace(" ", "")

    glyf = font['glyf']
    hmtx = font['hmtx']

    skipped = []

    # Left-align: set lsb to 0 and width to fixed_width if glyph fits
    for name in font.getGlyphOrder():
        g = glyf[name]
        # Skip composites for safety
        if hasattr(g, "isComposite") and g.isComposite():
            # We'll skip composites to avoid unpredictable results
            skipped.append(name)
            continue

        # Determine drawn width from glyph bounds
        drawn = 0
        if getattr(g, "xMin", None) is not None and getattr(g, "xMax", None) is not None:
            drawn = g.xMax - g.xMin
        if drawn <= 0:
            # No visible outline; just set to fixed width
            hmtx.metrics[name] = (fixed_width, 0)
            continue

        if drawn <= fixed_width:
            # Left align: no scaling, just reset bearings
            hmtx.metrics[name] = (fixed_width, 0)
        else:
            # Won't fit in the fixed box; skip this glyph
            skipped.append(name)

    # Report skipped glyphs
    if skipped:
        sys.stderr.write("Warning: Skipped glyphs that don't fit in the fixed width:\n")
        sys.stderr.write("  " + ", ".join(skipped[:50]))
        if len(skipped) > 50:
            sys.stderr.write(" ...")  # avoid overly long line
        sys.stderr.write("\n")

    # Update naming (Name table)
    name_table = font['name']
    name_table.setName(new_family, 1, 3, 1, 0x409)   # Font Family name (English)
    name_table.setName(new_fullname, 4, 3, 1, 0x409)  # Full font name
    name_table.setName(new_fontname, 6, 3, 1, 0x409)  # PostScript name

    font.save(dst)
    font.close()

if __name__ == "__main__":
    main()