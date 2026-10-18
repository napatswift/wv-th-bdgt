"""Correct the Unicode a PDF assigns to DilleniaUPC's Thai marks, before any text is read from it.

Budget PDFs draw Thai through DilleniaUPC embedded as Type0 Identity-H fonts, and their producers label some of its
mark glyphs wrongly in the ToUnicode map: Microsoft Thai PUA codes (FY2550-2552, and renumbered subsets in FY2570; other
fonts such as BrowalliaNew too), no label at all (FY2554, and the same font embedded as 'CIDFont+F1'/'F2' in FY2570),
and the nikhahit of sara am as a space (FY2570). Some volumes (FY2560, FY2567) embed it, and THSarabunPSK, with no
map at all. A glyph is recognised by its outline, not by its code or its font's name: some subsets are renumbered
and some are embedded nameless. See docs/thai-pdf-text-recovery-research.md.
"""
import hashlib
import io
import re
import struct

import fitz
from fontTools.ttLib import TTFont

from .glyph_outlines import GLYPHS

# Fonts draw sara am as nikhahit + sara aa, two glyphs, and label them so. No normalization form composes the pair
# (U+0E33's decomposition is a compatibility one), so it is composed here; a tone mark may sit on either side of
# the nikhahit and is kept before ำ, as Unicode orders it.
_SARA_AM = re.compile('\u0e4d([\u0e48-\u0e4b]?)\u0e32')


def compose_sara_am(text: str) -> str:
    return _SARA_AM.sub('\\1\u0e33', text)


# Microsoft Thai PUA positional forms -> the character each draws, as HarfBuzz's Thai shaper lists them
# (hb-ot-shaper-thai.cc): shifted-left, shifted-down(-left) and descender-less glyphs of ordinary Thai letters.
_PUA = {0xF700: '\u0e10', 0xF70F: '\u0e0d',
        0xF701: '\u0e34', 0xF702: '\u0e35', 0xF703: '\u0e36', 0xF704: '\u0e37',
        0xF710: '\u0e31', 0xF711: '\u0e4d', 0xF712: '\u0e47',
        0xF713: '\u0e48', 0xF714: '\u0e49', 0xF715: '\u0e4a', 0xF716: '\u0e4b', 0xF717: '\u0e4c',
        0xF705: '\u0e48', 0xF706: '\u0e49', 0xF707: '\u0e4a', 0xF708: '\u0e4b', 0xF709: '\u0e4c',
        0xF70A: '\u0e48', 0xF70B: '\u0e49', 0xF70C: '\u0e4a', 0xF70D: '\u0e4b', 0xF70E: '\u0e4c',
        0xF718: '\u0e38', 0xF719: '\u0e39', 0xF71A: '\u0e3a'}


_HEX = r'<([0-9A-Fa-f]+)>'
_BFCHAR = re.compile(r'beginbfchar(.*?)endbfchar', re.S)
_BFRANGE = re.compile(r'beginbfrange(.*?)endbfrange', re.S)


def _unicode(hexstr: str) -> str:
    return bytes.fromhex(hexstr).decode('utf-16-be', 'replace')


def read_cmap(cmap: str) -> dict[int, str]:
    """A ToUnicode CMap's code -> text entries."""
    mapping = {}
    for block in _BFCHAR.findall(cmap):
        for src, dst in re.findall(_HEX + r'\s*' + _HEX, block):
            mapping[int(src, 16)] = _unicode(dst)
    for block in _BFRANGE.findall(cmap):
        for lo, hi, dst in re.findall(_HEX + r'\s*' + _HEX + r'\s*(<[0-9A-Fa-f]+>|\[[^\]]*\])', block):
            lo, hi = int(lo, 16), int(hi, 16)
            if dst.startswith('['):
                for code, item in zip(range(lo, hi + 1), re.findall(_HEX, dst)):
                    mapping[code] = _unicode(item)
            else:
                start = _unicode(dst[1:-1])
                for offset in range(hi - lo + 1):
                    mapping[lo + offset] = start[:-1] + chr(ord(start[-1]) + offset)
    return mapping


def write_cmap(mapping: dict[int, str]) -> bytes:
    lines = ['/CIDInit /ProcSet findresource begin', '12 dict begin', 'begincmap',
             '/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def',
             '/CMapName /Adobe-Identity-UCS def', '/CMapType 2 def',
             '1 begincodespacerange', '<0000> <FFFF>', 'endcodespacerange']
    items = sorted(mapping.items())
    for i in range(0, len(items), 100):
        chunk = items[i:i + 100]
        lines.append(f'{len(chunk)} beginbfchar')
        lines += [f'<{code:04X}> <{text.encode("utf-16-be").hex().upper()}>' for code, text in chunk]
        lines.append('endbfchar')
    lines += ['endcmap', 'CMapName currentdict /CMap defineresource pop', 'end', 'end']
    return '\n'.join(lines).encode('ascii')


def outline_hash(font: TTFont, name: str) -> str | None:
    """A glyph's contours (glyf coordinates, contour ends, on-curve flags), or None for a glyph with none."""
    glyf = font['glyf']
    coords, ends, flags = glyf[name].getCoordinates(glyf)
    if not ends:
        return None
    return hashlib.sha1(repr((list(coords), list(ends), [f & 1 for f in flags])).encode()).hexdigest()[:16]


def _codes_by_gid(doc: fitz.Document, descendant: int, glyphs: int) -> dict[int, list[int]]:
    kind, value = doc.xref_get_key(descendant, 'CIDToGIDMap')
    if kind != 'xref':  # absent or /Identity: the code is the glyph id
        return {gid: [gid] for gid in range(glyphs)}
    data = doc.xref_stream(int(value.split()[0]))
    codes = {}
    for code, gid in enumerate(struct.unpack(f'>{len(data) // 2}H', data)):
        codes.setdefault(gid, []).append(code)
    return codes


def _advances(font: TTFont) -> dict[str, int]:
    try:
        return {name: advance for name, (advance, _) in font['hmtx'].metrics.items()}
    except Exception:  # a truncated hmtx table
        return {}


def glyph_labels(doc: fitz.Document, xref: int) -> dict[int, str]:
    """For a Type0 font embedding glyphs of a known outline (DilleniaUPC, THSarabunPSK), the code of each of its glyphs
    -> the text that glyph draws; one with no outline but an advance is a space. Empty for any other font."""
    descendant = int(re.findall(r'(\d+) 0 R', doc.xref_get_key(xref, 'DescendantFonts')[1])[0])
    program = doc.extract_font(descendant)[3] or doc.extract_font(xref)[3]
    try:
        font = TTFont(io.BytesIO(program), lazy=True)
        order = font.getGlyphOrder()
        font['glyf']
    except Exception:  # not embedded, or not a TrueType outline font
        return {}
    advances = _advances(font)
    codes = _codes_by_gid(doc, descendant, len(order))
    known, spaces = {}, {}
    for gid, name in enumerate(order):
        outline = outline_hash(font, name)
        if outline in GLYPHS:
            labels, char = known, GLYPHS[outline]
        elif outline is None and advances.get(name, 0) > 0:
            labels, char = spaces, ' '
        else:
            continue
        for code in codes.get(gid, ()):
            labels[code] = char
    return spaces | known if known else {}


def repair_dillenia(doc: fitz.Document) -> None:
    """Rewrite in memory the ToUnicode map of every Type0 Identity-H font so each glyph reads as what it draws:
    Microsoft Thai PUA labels become the Thai they stand for, and each glyph of a known outline gets its text, making
    the map a font has none of. Must run before any text is extracted: MuPDF keeps a font's map once loaded."""
    done = set()
    for pno in range(len(doc)):
        for xref, _, ftype, _, _, encoding in doc.get_page_fonts(pno):
            if xref in done or ftype != 'Type0' or encoding != 'Identity-H':
                continue
            done.add(xref)
            labels = glyph_labels(doc, xref)
            kind, value = doc.xref_get_key(xref, 'ToUnicode')
            if kind != 'xref':
                if labels:
                    cmap_xref = doc.get_new_xref()
                    doc.update_object(cmap_xref, '<<>>')
                    doc.update_stream(cmap_xref, write_cmap(labels))
                    doc.xref_set_key(xref, 'ToUnicode', f'{cmap_xref} 0 R')
                continue
            cmap_xref = int(value.split()[0])
            mapping = read_cmap(doc.xref_stream(cmap_xref).decode('latin-1'))
            mapping_pua = {code: text.translate(_PUA) for code, text in mapping.items()}
            # a map that labels the nikhahit ำ hides the sara aa drawn beside it (see drop_replacement_actualtext)
            fixed = mapping_pua | {code: char for code, char in labels.items()
                                   if not (char == '\u0e4d' and mapping_pua.get(code) == '\u0e33')}
            if fixed != mapping:
                doc.update_stream(cmap_xref, write_cmap(fixed))


# Some producers hide a glyph from the text layer by wrapping it in an /ActualText of U+FFFD instead of an empty
# string: FY2570 draws sara am as a nikhahit glyph labelled ำ plus a hidden sara aa, and doubled tone marks the same
# way. MuPDF reads such a span as U+FFFD, so it is made empty.
_FFFD_ACTUALTEXT = re.compile(rb'/ActualText\s*(?:\(\xfe\xff\xff\xfd\)|<FEFFFFFD>)', re.I)


def drop_replacement_actualtext(doc: fitz.Document) -> None:
    """Empty, in memory, every page's /ActualText that is U+FFFD. Must run before any text is extracted."""
    for page in doc:
        for xref in page.get_contents():
            stream = doc.xref_stream(xref)
            fixed = _FFFD_ACTUALTEXT.sub(b'/ActualText ()', stream)
            if fixed != stream:
                doc.update_stream(xref, fixed)
