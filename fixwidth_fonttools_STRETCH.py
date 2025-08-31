#!/usr/bin/env python3
import argparse
from fontTools.ttLib import TTFont
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

def main():
    parser = argparse.ArgumentParser(
        description="Stretch each glyph outline to fit a fixed width, then set side bearings to 0."
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

    # Read English family name robustly
    try:
        base_family = font['name'].getName(1, 3, 1, 0x409).toUnicode()
    except Exception:
        base_family = "Font"

    new_family = base_family + suffix
    new_fullname = new_family
    new_fontname = new_family.replace(" ", "")

    glyf = font['glyf']
    hmtx = font['hmtx']

    glyph_order = font.getGlyphOrder()
    glyphSet = font.getGlyphSet()

    # Stretch each glyph outline to fill the fixed width
    for name in glyph_order:
        g = glyf[name]
        # Skip composites if present
        if hasattr(g, "isComposite") and g.isComposite():
            continue

        # Compute current drawn width from glyph bounds
        if getattr(g, "xMin", None) is not None and getattr(g, "xMax", None) is not None:
            drawn = g.xMax - g.xMin
        else:
            drawn = 0

        if drawn > 0:
            s = float(fixed_width) / float(drawn)
            pen = TTGlyphPen(font.getGlyphSet())
            tpen = TransformPen(pen, (s, 0, 0, 1, 0, 0))
            # Pass the glyf table as required by newer FontTools
            g.draw(tpen, glyf)
            new_glyph = pen.glyph()
            glyf[name] = new_glyph

        # Update horizontal metrics
        hmtx.metrics[name] = (fixed_width, 0)

    # Update naming (Name table)
    name_table = font['name']
    name_table.setName(new_family, 1, 3, 1, 0x409)   # Font Family name
    name_table.setName(new_fullname, 4, 3, 1, 0x409)  # Full font name
    name_table.setName(new_fontname, 6, 3, 1, 0x409)  # PostScript name

    font.save(dst)
    font.close()

if __name__ == "__main__":
    main()