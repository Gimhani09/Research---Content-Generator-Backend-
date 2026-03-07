"""Check fonts for Sinhala OpenType support"""
from fontTools.ttLib import TTFont
import os

fonts_to_check = [
    ("D:/Research Frontend/content-generator-backend/fonts/0KDBOLIDDA bold.ttf", "0KDBOLIDDA Bold"),
    ("d:/content_generator/fonts/4u-Gemunu x.ttf", "4u-Gemunu x"),
    ("d:/content_generator/fonts/NotoSansSinhala-Variable.ttf", "NotoSansSinhala"),
]

for path, name in fonts_to_check:
    if not os.path.isfile(path):
        print(f"\n{name}: FILE NOT FOUND at {path}")
        continue
    try:
        font = TTFont(path)
        tables = list(font.keys())
        has_gsub = "GSUB" in tables
        has_gpos = "GPOS" in tables
        has_gdef = "GDEF" in tables

        # Check for Sinhala cmap entries (U+0D80-U+0DFF)
        cmap = font.getBestCmap()
        sinhala_chars = [cp for cp in cmap.keys() if 0x0D80 <= cp <= 0x0DFF]

        # Check GSUB for Sinhala-specific lookups
        gsub_scripts = []
        if has_gsub:
            gsub = font["GSUB"]
            if hasattr(gsub.table, "ScriptList") and gsub.table.ScriptList:
                gsub_scripts = [sr.ScriptTag for sr in gsub.table.ScriptList.ScriptRecord]

        gpos_scripts = []
        if has_gpos:
            gpos = font["GPOS"]
            if hasattr(gpos.table, "ScriptList") and gpos.table.ScriptList:
                gpos_scripts = [sr.ScriptTag for sr in gpos.table.ScriptList.ScriptRecord]

        has_sinh_gsub = "sinh" in gsub_scripts
        has_sinh_gpos = "sinh" in gpos_scripts

        print(f"\n{'='*50}")
        print(f"  FONT: {name}")
        print(f"  File: {path}")
        print(f"  Size: {os.path.getsize(path)//1024}KB")
        print(f"{'='*50}")
        print(f"  GSUB (glyph substitution):  {'YES' if has_gsub else 'NO'}")
        print(f"  GPOS (glyph positioning):   {'YES' if has_gpos else 'NO'}")
        print(f"  GDEF (glyph definition):    {'YES' if has_gdef else 'NO'}")
        print(f"  GSUB scripts: {gsub_scripts}")
        print(f"  GPOS scripts: {gpos_scripts}")
        print(f"  Sinhala chars (U+0D80-0DFF): {len(sinhala_chars)} glyphs")
        print(f"  'sinh' in GSUB: {'YES' if has_sinh_gsub else 'NO'}")
        print(f"  'sinh' in GPOS: {'YES' if has_sinh_gpos else 'NO'}")

        # Verdict
        if has_sinh_gsub and sinhala_chars >= 50:
            print(f"  VERDICT: FULL SINHALA SUPPORT - Safe for poster titles")
        elif sinhala_chars > 0 and not has_sinh_gsub:
            print(f"  VERDICT: HAS SINHALA GLYPHS BUT NO SHAPING - Will break conjuncts!")
        elif sinhala_chars == 0:
            print(f"  VERDICT: NO SINHALA GLYPHS - Latin only font")
        else:
            print(f"  VERDICT: PARTIAL SUPPORT - May have issues")

        font.close()
    except Exception as e:
        print(f"\n{name}: ERROR - {e}")
        import traceback
        traceback.print_exc()
