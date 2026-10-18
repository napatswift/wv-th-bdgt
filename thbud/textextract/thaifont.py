"""Correct the Unicode a PDF assigns to DilleniaUPC's Thai marks, before any text is read from it.

Budget PDFs draw Thai through DilleniaUPC embedded as Type0 Identity-H fonts, and their producers label some of its
mark glyphs wrongly in the ToUnicode map: Microsoft Thai PUA codes (FY2550-2552, and renumbered subsets in FY2570),
no label at all (FY2554, and the same font embedded as 'CIDFont+F1'/'F2' in FY2570), and the nikhahit of sara am as a
space (FY2570). A glyph is recognised by its outline, not by its code or its font's name: some subsets are renumbered
and some are embedded nameless. See docs/thai-pdf-text-recovery-research.md.
"""
import hashlib
import io
import re
import struct

import fitz
from fontTools.ttLib import TTFont

from .dillenia_marks import MARKS

# Fonts draw sara am as nikhahit + sara aa, two glyphs, and label them so. No normalization form composes the pair
# (U+0E33's decomposition is a compatibility one), so it is composed here; a tone mark may sit on either side of
# the nikhahit and is kept before ำ, as Unicode orders it.
_SARA_AM = re.compile('\u0e4d([\u0e48-\u0e4b]?)\u0e32')


def compose_sara_am(text: str) -> str:
    return _SARA_AM.sub('\\1\u0e33', text)


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


def mark_labels(doc: fitz.Document, xref: int) -> dict[int, str]:
    """For a Type0 font, the code of each DilleniaUPC mark glyph it embeds -> the character that glyph draws."""
    descendant = int(re.findall(r'(\d+) 0 R', doc.xref_get_key(xref, 'DescendantFonts')[1])[0])
    program = doc.extract_font(descendant)[3] or doc.extract_font(xref)[3]
    try:
        font = TTFont(io.BytesIO(program), lazy=True)
        order = font.getGlyphOrder()
        font['glyf']
    except Exception:  # not embedded, or not a TrueType outline font
        return {}
    labels = {}
    codes = _codes_by_gid(doc, descendant, len(order))
    for gid, name in enumerate(order):
        char = MARKS.get(outline_hash(font, name))
        if char:
            for code in codes.get(gid, ()):
                labels[code] = char
    return labels


def repair_dillenia(doc: fitz.Document) -> None:
    """Rewrite in memory the ToUnicode map of every Type0 Identity-H font that embeds DilleniaUPC mark glyphs, so
    each reads as what it draws. Must run before any text is extracted: MuPDF keeps a font's map once loaded."""
    done = set()
    for pno in range(len(doc)):
        for xref, _, ftype, _, _, encoding in doc.get_page_fonts(pno):
            if xref in done or ftype != 'Type0' or encoding != 'Identity-H':
                continue
            done.add(xref)
            kind, value = doc.xref_get_key(xref, 'ToUnicode')
            if kind != 'xref':
                continue
            labels = mark_labels(doc, xref)
            if not labels:
                continue
            cmap_xref = int(value.split()[0])
            mapping = read_cmap(doc.xref_stream(cmap_xref).decode('latin-1'))
            fixed = mapping | labels
            if fixed != mapping:
                doc.update_stream(cmap_xref, write_cmap(fixed))


# Some producers hide a glyph from the text layer by wrapping it in an /ActualText of U+FFFD instead of an empty
# string: FY2570 draws sara am as a glyph labelled ำ plus a hidden sara aa, and doubled tone marks the same way.
# MuPDF reads such a span as U+FFFD, so it is made empty.
_FFFD_ACTUALTEXT = re.compile(rb'/ActualText\s*(?:\(\xfe\xff\xff\xfd\)|<FEFFFFFD>)', re.I)


def drop_replacement_actualtext(doc: fitz.Document) -> None:
    """Empty, in memory, every page's /ActualText that is U+FFFD. Must run before any text is extracted."""
    for page in doc:
        for xref in page.get_contents():
            stream = doc.xref_stream(xref)
            fixed = _FFFD_ACTUALTEXT.sub(b'/ActualText ()', stream)
            if fixed != stream:
                doc.update_stream(xref, fixed)
