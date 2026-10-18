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


# Typists' habits the text keeps: two sara e for sara ae, and a tone mark or thanthakhat typed before the vowel above
# or below its consonant (Unicode, and written Thai, put the vowel first).
_TWO_SARA_E = re.compile('\u0e40\u0e40(?=[\u0e01-\u0e2e])')
_TONE_BEFORE_VOWEL = re.compile('([\u0e48-\u0e4c])([\u0e31\u0e34-\u0e3a])')
# a mark (vowel above/below, tone, thanthakhat, ...) cannot begin a word
STARTS_WITH_MARK = re.compile('[\u0e31\u0e34-\u0e3a\u0e47-\u0e4e]')


def normalize_thai(text: str) -> str:
    """Typed Thai in the order written Thai uses: sara am composed, 'เเ' as แ, a tone or ์ after its vowel."""
    text = _TWO_SARA_E.sub('\u0e41', text)
    text = _TONE_BEFORE_VOWEL.sub('\\2\\1', text)
    return compose_sara_am(text)


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


def repair_dillenia(doc: fitz.Document) -> dict[int, set[int]]:
    """Rewrite in memory the ToUnicode map of every Type0 Identity-H font so each glyph reads as what it draws:
    Microsoft Thai PUA labels become the Thai they stand for, and each glyph of a known outline gets its text, making
    the map a font has none of. Must run before any text is extracted: MuPDF keeps a font's map once loaded.
    Returns, per font, the codes whose glyphs were recognised by outline."""
    done, recognised = set(), {}
    for pno in range(len(doc)):
        for xref, _, ftype, _, _, encoding in doc.get_page_fonts(pno):
            if xref in done or ftype != 'Type0' or encoding != 'Identity-H':
                continue
            done.add(xref)
            labels = glyph_labels(doc, xref)
            if labels:
                recognised[xref] = set(labels)
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
            fixed = {code: text.translate(_PUA) for code, text in mapping.items()} | labels
            if fixed != mapping:
                doc.update_stream(cmap_xref, write_cmap(fixed))
    return recognised


_WHITE = b' \t\r\n\x0c\x00'
_DELIMITERS = b'()<>[]{}/%'
_ESCAPES = {ord('n'): b'\n', ord('r'): b'\r', ord('t'): b'\t', ord('b'): b'\b', ord('f'): b'\f'}


def _lex(data: bytes):
    """(kind, start, end) of each token of a content stream: 'str', 'hex', '<<', '>>', '[', ']', 'name', 'word'.
    Inline image data (BI ... ID <data> EI) is skipped."""
    i, n = 0, len(data)
    while i < n:
        c = data[i]
        if c in _WHITE:
            i += 1
        elif c == 0x25:  # %comment
            j = data.find(b'\n', i)
            i = n if j < 0 else j
        elif c == 0x28:  # (literal string), balanced parentheses, backslash escapes
            start, depth = i, 0
            while i < n:
                if data[i] == 0x5C:
                    i += 2
                    continue
                depth += {0x28: 1, 0x29: -1}.get(data[i], 0)
                i += 1
                if depth == 0:
                    break
            yield 'str', start, i
        elif data.startswith(b'<<', i) or data.startswith(b'>>', i):
            yield data[i:i + 2].decode(), i, i + 2
            i += 2
        elif c == 0x3C:  # <hex string>
            j = data.find(b'>', i)
            j = n if j < 0 else j + 1
            yield 'hex', i, j
            i = j
        elif c in b'[]{}':
            yield chr(c), i, i + 1
            i += 1
        else:
            start = i
            i += 1
            while i < n and data[i] not in _WHITE and data[i] not in _DELIMITERS:
                i += 1
            if data[start:i] == b'ID':  # inline image: its data runs to an EI between white space
                m = re.compile(rb'\sEI(?=[\s]|$)').search(data, i + 1)
                i = n if m is None else m.end()
                continue
            yield ('name' if c == 0x2F else 'word'), start, i


def _string_bytes(token: bytes) -> bytes:
    if token.startswith(b'<'):
        return bytes.fromhex(re.sub(rb'[^0-9A-Fa-f]', b'', token[1:-1]).decode().ljust(2, '0'))
    out, i, body = bytearray(), 0, token[1:-1]
    while i < len(body):
        c = body[i]
        if c != 0x5C:
            out.append(c)
            i += 1
            continue
        nxt = body[i + 1] if i + 1 < len(body) else None
        if nxt is not None and 0x30 <= nxt <= 0x37:
            octal = re.match(rb'[0-7]{1,3}', body[i + 1:]).group()
            out.append(int(octal, 8) & 0xFF)
            i += 1 + len(octal)
        elif nxt in (0x0A, 0x0D):  # line continuation
            i += 2 + (nxt == 0x0D and body[i + 2:i + 3] == b'\n')
        else:
            out += _ESCAPES.get(nxt, bytes([nxt]) if nxt is not None else b'')
            i += 2
    return bytes(out)


_REPLACEMENT = b'\xfe\xff\xff\xfd'  # U+FFFD as a UTF-16BE text string with its byte order mark
_OPERAND_WORD = re.compile(rb'[-+.\d]+$|true$|false$|null$')


def _actualtext_edits(data: bytes, fonts: dict[bytes, int], recognised: dict[int, set[int]], state: dict):
    """Byte ranges of `data` to replace: the /ActualText entry of each marked-content span whose glyphs were all
    recognised by outline is dropped; one of U+FFFD over glyphs that were not is emptied."""
    edits, operands = [], []
    stack = state.setdefault('stack', [])
    for kind, start, end in _lex(data):
        if kind != 'word' or _OPERAND_WORD.match(data, start, end):
            operands.append((kind, start, end))
            continue
        op = data[start:end]
        if op == b'Tf' and len(operands) >= 2 and operands[-2][0] == 'name':
            state['font'] = fonts.get(data[operands[-2][1] + 1:operands[-2][2]])
        elif op == b'BDC':
            entry = None
            for k, (kd, s0, e0) in enumerate(operands):
                if kd == 'name' and data[s0:e0] == b'/ActualText' and k + 1 < len(operands):
                    kd2, s1, e1 = operands[k + 1]
                    if kd2 in ('str', 'hex'):
                        entry = (s0, e1, _string_bytes(data[s1:e1]))
            stack.append({'entry': entry, 'glyphs': 0, 'known': True})
        elif op == b'BMC':
            stack.append({'entry': None, 'glyphs': 0, 'known': True})
        elif op == b'EMC' and stack:
            span = stack.pop()
            if stack:
                stack[-1]['glyphs'] += span['glyphs']
                stack[-1]['known'] &= span['known']
            if span['entry'] is not None:
                s0, e1, text = span['entry']
                if span['glyphs'] and span['known']:
                    edits.append((s0, e1, b''))
                elif text in (_REPLACEMENT, _REPLACEMENT[2:]):
                    edits.append((s0, e1, b'/ActualText ()'))
        elif op in (b'Tj', b"'", b'"', b'TJ') and stack:
            strings = [data[s:e] for kd, s, e in operands if kd in ('str', 'hex')]
            codes = b''.join(_string_bytes(t) for t in strings)
            known = recognised.get(state.get('font'))
            n = len(codes) // 2
            top = stack[-1]
            top['glyphs'] += n
            if n and (known is None or any(int.from_bytes(codes[2 * i:2 * i + 2], 'big') not in known
                                           for i in range(n))):
                top['known'] = False
        operands = []
    return edits


def drop_redundant_actualtext(doc: fitz.Document, recognised: dict[int, set[int]]) -> None:
    """Drop, in memory, the /ActualText of every marked-content span whose glyphs are all recognised by outline, so
    they read as the glyphs they draw; empty one of U+FFFD over other glyphs. Must run before any text is extracted.

    FY2568-2570 producers wrap each cluster's text ('ลื่') around its consonant glyph alone and draw its marks after
    the span, so the marks read twice; and hide a glyph (the sara aa beside a nikhahit) with an /ActualText of U+FFFD
    instead of an empty string, which MuPDF reads as U+FFFD."""
    for page in doc:
        fonts = {ref.encode(): xref for xref, _, _, _, ref, _ in page.get_fonts()}
        state = {}
        for xref in page.get_contents():
            data = doc.xref_stream(xref)
            edits = _actualtext_edits(data, fonts, recognised, state)
            if not edits:
                continue
            out, last = bytearray(), 0
            for s0, e1, repl in sorted(edits):
                out += data[last:s0] + repl
                last = e1
            doc.update_stream(xref, bytes(out + data[last:]))
