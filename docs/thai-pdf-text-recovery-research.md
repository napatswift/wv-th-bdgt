# Recovering Thai text from bb.go.th budget PDFs

Research date: 2026-10-18. Corpus: six sample volumes (FY2550, 2552, 2554, 2558, 2562, 2570). Reader under study: `thbud/textextract/documenttext.py` (`DocumentText`, PyMuPDF 1.26.7 / MuPDF 1.26.12) and `text.py` (`LineText._join_words`, `WordText.fix_pdf_text`). Scripts used for the measurements are in the session scratchpad, not in this repo.

## Outcome (implemented; supersedes the glyph-ID table below)

A wider check (10 volumes, including FY2570 เล่มที่ ๔, ๑๑, ๑๓(๑)) found **glyph IDs are not unique to glyphs**: those
volumes also embed DilleniaUPC as *compacted* Type0 subsets (73–126 glyphs, `CIDToGIDMap /Identity`), where a code is
the compacted index. A `(family, style, gid)` table would relabel the wrong glyphs there. Only the full-numbering
subsets (224 or 362 glyphs) keep one outline per gid.

What the reader does instead (`thbud/textextract/thaifont.py`, called by `DocumentText` right after opening a PDF):

- **Marks are recognised by outline.** In every Type0 Identity-H font, whatever its name, each glyph's raw `glyf`
  contours are hashed and looked up in `dillenia_marks.py`: 41 DilleniaUPC Thai mark outlines → the character each
  draws, generated from the full-numbering subsets, with no outline shared by glyphs that read differently. Matching
  codes are relabelled in the font's ToUnicode map, in memory, before MuPDF reads any text. This covers the
  full-numbering subsets, the nameless `CIDFont+F1/F2` (same outlines at the same ids) and the compacted subsets
  (PUA-labelled marks).
- **Sara am** is composed (`ํ` + optional tone + `า` → tone + `ำ`) on every word the loader returns.
- `LineText._join_words` / `WordText.fix_pdf_text` are removed: the split they patched no longer happens.

Measured on 10 volumes (~5,600 pages): PUA 25,320 → 128 (AngsanaUPC on a few 2550 pages, and cover fonts), Latin-1
tone marks 7,611 → 0, `ํา` 16,778 → 0, mark-led word fragments 30,951 → 7 (stray marks in the source). th-budget's
`parse_pdf` on 129 real §7 unit ranges (TOC + footer offset): structure and every amount identical, 4,426 item names
corrected. Not covered: AngsanaUPC and other UPC fonts (same method, needs their outlines); 7 Bold PUA-era marks never
seen in the samples (Bold 100, 102, 105, 107, 108, 109, 126); image pages (covers only, so far).

## Summary (original research, before the wider check)

- **Text pages: read glyph IDs, not the ToUnicode text.** Every sample is set in DilleniaUPC Regular/Bold. A glyph ID always names the same outline across all years and subsets (verified by outline hashing; see Corpus evidence). The Unicode emitted for those glyphs is wrong in three distinct ways: Microsoft Thai PUA (2550–2552), missing ToUnicode entries that PyMuPDF turns into Latin-1 `É Ê Ë Ì Í` (2554), and nikhahit mapped to U+0020 (2570).
- Build a `(family, style, gid) → Unicode` table by majority vote over the corpus. Hook it into `DocumentText.words_loader` via `page.get_texttrace()`, then apply one text-level step: compose `U+0E4D U+0E32` into `U+0E33`.
- **Text-level normalization alone is a strong, cheap fallback.** Map the PUA with `str.translate`, map Latin-1 `É–Í` after a Thai character to tone marks, and apply the sara-am rules. That raises the dictionary hit rate from 0.856–0.969 to 0.982–0.998 on every sample year. Use it for fonts that are not in the table.
- **Image pages (and documents that fail the gid check) go to OCR.** Generic Tesseract `tha` at 300 dpi is fast (0.9–1.7 s/page per core). On prose-like pages it loses about 1–3% of characters. On ruled table pages it loses 24–36%, and it makes Thai confusable and digit substitutions (`15,775,000` read as `16,775,000`).
- Next steps for OCR: fine-tune Tesseract on DilleniaUPC lines, using line crops from the repaired text-layer pages as free ground truth, and pre-process the table ruling. Measure CER with the harness described below before choosing between that and a Thai VLM OCR such as Typhoon OCR, which needs a GPU.
- Route each page with cheap signals: no text layer or image coverage → OCR; a font in the gid table → remap; otherwise text normalization, with OCR when the dictionary hit rate stays low.

## 1. Corpus evidence

### 1.1 Producers and fonts

| FY | Creator / Producer (PDF metadata) | DilleniaUPC embeddings |
|---|---|---|
| 2550 | Acrobat PDFMaker 7.0.7 for Excel / Acrobat Distiller 7.0.5 | TrueType simple (WinAnsi) + Type0 Identity-H subsets |
| 2552 | Adobe Acrobat 7.08 / Image Conversion Plug-in | same |
| 2554 | PScript5.dll 5.2 / Acrobat Distiller 7.0 | same |
| 2558 | PScript5.dll 5.2.2 / Acrobat Distiller 9.0.0 | same (+ BrowalliaNew, Arial Identity-H) |
| 2562 | PScript5.dll 5.2.2 / Acrobat Distiller 11.0 | same (+ DBComYardX, AdobeThai on a few pages) |
| 2570 | Adobe InDesign 21.0 (Macintosh) / Adobe PDF Library 18.0 | same (+ THSarabunPSK, PSLThaiCommonPro, `CIDFont+F1/F2` on some pages) |

None of the samples is a direct "MS Word → PDF" export. They are Excel/Word printed through the Adobe PostScript driver into Distiller (2550–2562), or InDesign (2570).

- **Embedded fonts have no glyph names and no Thai cmap.**
  - Embedded subsets use `post` format 3.0, so there are no glyph names.
  - Type0 subsets have no `cmap`.
  - The simple-TrueType subsets of 2550–2562 have (1,0)/(3,1) cmaps that cover only the WinAnsi codes.
  - The 2570 subsets carry a (3,1) cmap with Thai entries, for example gid 206 → U+0E4D.
- **No reference font is installed locally.** DilleniaUPC is not on this Mac: nothing in `/System/Library/Fonts`, `/Library/Fonts`, `~/Library/Fonts`, or the Office `DFonts` folder (which holds only `cordia.ttc`, `tahoma*.ttf`). Word shows it only as a cloud-font preview. Microsoft lists it as shipping with Windows XP (v2.20), Vista (v5.00) and 7–11, and as an Office cloud font ([MS DilleniaUPC page](https://learn.microsoft.com/en-us/typography/font-list/dilleniaupc)). So I could not do a round trip against a reference cmap.

### 1.2 Glyph-ID stability (outline hashing)

> Superseded: true only for full-numbering subsets. Compacted subsets in FY2570 renumber glyphs; see Outcome.

**Coordinator's verification:** across the six volumes, 323 (style, gid) pairs carry outlines, with **0 conflicts**. Hashes were taken with fontTools `RecordingPen` per (Regular/Bold, gid).

**My independent spot check agrees, with one discrepancy on glyph counts.**
- I hashed 35 key gids (3, 100–127, 132, 151, 181, 201–206, 345–346) in every embedded DilleniaUPC subset: Type0 and simple TrueType, Regular and Bold separately.
- The result was exactly one outline hash per (style, gid) across all years and subsets.
- **Discrepancy with the coordinator's "362 slots everywhere":**
  - In my extraction, `maxp.numGlyphs` is **224** for every 2550 and 2552 subset and for one 2554 subset.
  - It is **362** for 2554 (most subsets) through 2570.
  - Both values mean slots are padded (GIDs not renumbered). They probably reflect two font versions (XP v2.20 vs Vista+ v5.00; this attribution is unverified).
  - Where the two versions overlap, the gids carry identical outlines.

**Why the GIDs survive subsetting:**
- For Type0 fonts, Identity-H plus the default `CIDToGIDMap /Identity` means CID = GID ([ISO 32000-1 Table 117](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf)).
- For simple TrueType fonts, the code→glyph mapping goes through the embedded font's cmap (§9.6.6.4). A subsetter is therefore free to renumber.
- Distiller and Adobe PDF Library kept the original GIDs here (padded `glyf`/`loca`), as shown by the stable outline hashes.
- **Unverified:** I found no first-party Adobe or Microsoft document promising this behaviour. Treat it as observed, and guard it with the outline-hash check (§4.3).

### 1.3 gid → Unicode as emitted, and the correct value

From `page.get_texttrace()` over all pages. Counts are summed over all six years, Regular + Bold. Only glyphs with a defect are listed. All other DilleniaUPC gids (3 = space, 11–96 ASCII, 132–200 Thai letters and vowels, 211–214 Thai digits) map consistently and correctly in every year.

| gid | Correct | Emitted (FY: code point) |
|---|---|---|
| 100 | U+0E34 ิ | 2550/2552: U+F701 |
| 101 | U+0E35 ี | 2550/2552/2554: U+F702 |
| 102 | U+0E36 ึ | 2550/2552: U+F703 |
| 103 | U+0E37 ื | 2550/2552: U+F704 |
| 105 | U+0E48 ่ | 2550/2552: U+F705 |
| 106 | U+0E49 ้ | 2550/2552: U+F706 |
| 107 | U+0E4A ๊ | 2550: U+F707 |
| 108 | U+0E4B ๋ | 2550: U+F708 |
| 109 | U+0E4C ์ | 2552: U+F709 |
| 110 | U+0E48 ่ | 2550/2552: U+F70A; 2554: U+0E48 (4,028) + U+F70A (4); 2558–2570: U+0E48 |
| 111 | U+0E49 ้ | 2550/2552: U+F70B; 2554+: U+0E49 |
| 112 | U+0E4A ๊ | 2550/2552: U+F70C; 2554+: U+0E4A |
| 113 | U+0E4B ๋ | 2550/2552: U+F70D; 2554+: U+0E4B |
| 114 | U+0E4C ์ | 2550/2552: U+F70E; 2554+: U+0E4C |
| 123 | U+0E31 ั | 2550/2552: U+F710 |
| 125 | U+0E47 ็ | 2550/2552: U+F712 |
| 126 | U+0E48 ่ | 2550: U+F713 |
| 127 | U+0E49 ้ | 2550/2552: U+F714 |
| 201–205 | U+0E48–U+0E4C | correct, except 2554: **missing ToUnicode entry** (2,042 + 2,446 + 3 + 1 + 30 hits) and 2562: 13 hits |
| 206 | U+0E4D ํ | 2550–2562: U+0E4D; **2570: U+0020** (ToUnicode literally `<00CD> <00CE> [<0E4C> <0020>]`) |

The PUA columns follow the Microsoft table quoted in §3.1 exactly: F70A–F70E = "shift down" tones, F705–F709 = "shift down-left", F701–F704/F710/F712 = "shift left" vowels.

### 1.4 What the reader actually receives (`page.get_text_words()`)

- **2554 missing entries come out as Latin-1, not U+FFFD.** For a code with no ToUnicode entry, MuPDF's interpreter yields U+FFFD (`source/pdf/pdf-op-run.c`, lines ~1421–1440). PyMuPDF's default `TEXT_USE_CID_FOR_UNKNOWN_UNICODE` (128) then substitutes the raw code. Because CID = GID, gid 201 arrives as `É` (U+00C9): `ฉบับทีÉ` = ฉบับที่. That flag is on in `TEXTFLAGS_WORDS` and the other extraction defaults ([PyMuPDF vars](https://pymupdf.readthedocs.io/en/latest/vars.html)). With the flag cleared, the same word reads `ฉบับที�`.
- **Sara am arrives decomposed in every year.** It is `U+0E4D U+0E32`, because the font draws ำ as two glyphs (206 + 181). That is the Uniscribe "AM … broken into two glyphs" model ([MS Thai OpenType](https://learn.microsoft.com/en-us/typography/script-development/thai)). Zero native U+0E33 come from DilleniaUPC.
- **Other fonts in 2570 show the same Latin-1 artifact.** `CIDFont+F1/F2` produce `ทีÉคาดว่า`. THSarabunPSK emits `ำ` + U+FFFD pairs (131 + 8).

| FY | pages | PUA chars | Latin-1 É–Í | `ํา` pairs | space+(tone)+า splits | dict-hit before → after text normalization |
|---|---|---|---|---|---|---|
| 2550 | 311 | 8,411 (305 pages) | 0 | 1,056 | 0 | 0.887 → 0.982 |
| 2552 | 464 | 16,329 (462 pages) | 0 | 2,129 | 0 | 0.856 → 0.994 |
| 2554 | 243 | 17 | 4,519 | 1,820 | 0 | 0.925 → 0.984 |
| 2558 | 432 | 0 | 0 | 3,176 | 0 | 0.960 → 0.998 |
| 2562 | 800 | 2 | 13 | 10,058 | 0 | 0.937 → 0.997 |
| 2570 | 644 | 2 | 482 | 226 | 4,292 (554 pages) | 0.969 → 0.998 |

- **Dictionary hit rate:** share of Thai characters inside PyThaiNLP `newmm` tokens found in `thai_words()`.
- **"After"** means the text-level rules in §4.2. Residual PUA after normalization: 0 in every year. Residual Latin-1: 1 (2570).

### 1.5 Defects in the current reader code (`text.py`)

- **Tone-led fragments are not converted.** `fix_pdf_text` only rewrites a *leading* `า`. A tone-led fragment such as `่า` is joined unchanged, so 2570 `ต ่า` becomes `ต่า`, not `ต่ำ`.
- **`ํา` is joined but never composed** to U+0E33.
- **The `_join_words` mark list is incomplete.** It tests U+0E48 twice and omits U+0E4A (mai tri).
- **PUA and Latin-1 tone marks pass through untouched.**

## 2. How PDF tools map codes to Unicode, and why none fixes this

- **ISO 32000-1 §9.10.2 order.**
  1. Use the ToUnicode CMap.
  2. Otherwise, for simple fonts with standard encodings, use glyph names and the Adobe Glyph List.
  3. Otherwise, for predefined CJK CMaps/collections, use `Registry-Ordering-UCS2`.
  4. "If these methods fail … there is no way to determine what the character code represents."

  The spec defines no fallback to the font's own cmap or `post` table for Identity-H ([PDF32000_2008.pdf, p. 293–294](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf)). §9.6.6.4 lets readers use `post` glyph names only for *glyph selection* in TrueType fonts.
- **MuPDF** (`pdf_load_to_unicode`). It uses the ToUnicode stream, else a named CMap, else the CJK UCS2 tables, else glyph names for simple fonts. The code says `/* TODO: synthesize a ToUnicode if it's a freetype font with cmap and/or post tables */` ([pdf-unicode.c](https://github.com/ArtifexSoftware/mupdf/blob/master/source/pdf/pdf-unicode.c)). At render time, an unmapped code becomes U+FFFD ([pdf-op-run.c](https://github.com/ArtifexSoftware/mupdf/blob/master/source/pdf/pdf-op-run.c)).
- **pdf.js** (`buildToUnicode`). If a ToUnicode map exists it wins; simple fonts get an encoding-based fallback for holes. A composite Identity font without ToUnicode gets `IdentityToUnicodeMap` ("The viewer's choice") ([evaluator.js](https://github.com/mozilla/pdf.js/blob/master/src/core/evaluator.js)).
- **PDFBox** (`PDType0Font.toUnicode`). It uses ToUnicode. If the ToUnicode exists but lacks the code, it returns the code itself (identity), which is the same artifact as PyMuPDF's `É`. Only when there is no ToUnicode does it try the embedded TrueType Unicode cmap (PDFBOX-5324) ([PDType0Font.java](https://github.com/apache/pdfbox/blob/trunk/pdfbox/src/main/java/org/apache/pdfbox/pdmodel/font/PDType0Font.java)).
- **poppler.** For simple fonts, the encoding fills holes and ToUnicode overwrites. For CID fonts, it uses ToUnicode, else identity for Adobe-Identity/UCS ([GfxFont.cc](https://gitlab.freedesktop.org/poppler/poppler/-/blob/master/poppler/GfxFont.cc)).

**Consequence.** All four libraries trust an *explicit* ToUnicode entry, so none repairs 2570's `206 → U+0020` or 2550–2552's PUA. Repair has to happen in the reader. The 2570 embedded cmap (206 → U+0E4D) would fix 2570 if a tool inverted it. But no reader does this while a ToUnicode is present, and the 2550–2562 subsets carry no Thai cmap to invert.

**Glyph-outline hashing in the literature:** I found no primary-source tool or paper that recovers Unicode by matching embedded glyph outlines against a reference font. Searches turned up only vendor claims (unverified). The approach is simple to implement with fontTools pens ([fontTools RecordingPen](https://fonttools.readthedocs.io/en/latest/pens/recordingPen.html)). Its robustness here rests on our own evidence (§1.2): byte-identical outlines because the same font files were subset without hinting changes. Across *different* font versions or rasterizers, exact hashes would fail and a tolerant shape metric would be needed (not evaluated).

## 3. Thai specifics

### 3.1 Microsoft Thai PUA (authoritative table)

HarfBuzz's Thai shaper carries the Windows and Mac PUA forms as `{Unicode, Windows PUA, Mac PUA}` ([hb-ot-shaper-thai.cc](https://github.com/harfbuzz/harfbuzz/blob/main/src/hb-ot-shaper-thai.cc)). Quoted:

```
SD  (shift down):      {0E48,F70A,F88B} {0E49,F70B,F88E} {0E4A,F70C,F891} {0E4B,F70D,F894} {0E4C,F70E,F897}
                       {0E38,F718,F89B} {0E39,F719,F89C} {0E3A,F71A,F89D}
SDL (shift down-left): {0E48,F705,F88C} {0E49,F706,F88F} {0E4A,F707,F892} {0E4B,F708,F895} {0E4C,F709,F898}
SL  (shift left):      {0E48,F713,F88A} {0E49,F714,F88D} {0E4A,F715,F890} {0E4B,F716,F893} {0E4C,F717,F896}
                       {0E31,F710,F884} {0E34,F701,F885} {0E35,F702,F886} {0E36,F703,F887} {0E37,F704,F888}
                       {0E47,F712,F889} {0E4D,F711,F899}
RD  (remove descender):{0E0D,F70F,F89A} {0E10,F700,F89E}
```

The table covers every U+F700–U+F71A code; inverting it is lossless for text purposes. The Mac column (U+F884–F89E) is the Apple variant. No Mac PUA occurred in the samples. Microsoft's own Thai OpenType page does not list the PUA codes; it describes the ccmp decomposition of sara am and the removal of the yo ying descender ([MS Thai OpenType](https://learn.microsoft.com/en-us/typography/script-development/thai)).

### 3.2 Sara am and normalization

- **Decomposition.** `0E33;THAI CHARACTER SARA AM;Lo;0;L;<compat> 0E4D 0E32` is a **compatibility** decomposition, not a canonical one ([UnicodeData.txt](https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt)).
  - NFC and NFD leave U+0E33 alone.
  - NFKC and NFKD turn it into `ํา`, the *opposite* of what we want.
  - UAX #15 says KC/KD "must not be blindly applied to arbitrary text" ([UAX #15 rev 58](https://www.unicode.org/reports/tr15/tr15-58.html)).
  - So compose `U+0E4D U+0E32 → U+0E33` explicitly; no normalization form does it.
- **Order with tone marks.** The Unicode Thai section uses `<U+0E48 MAI EK, U+0E33 SARA AM>`, tone before sara am, and says the nikhahit of sara am renders *below* preceding tones ([Unicode 18.0 §16.1](https://www.unicode.org/versions/Unicode18.0.0/core-spec/chapter-16/)).
  - Nikhahit has ccc = 0 and tones have ccc = 107, so normalization will not reorder `ํ ่ า` vs `่ ํ า`.
  - The compose rule must therefore accept both orders and emit `tone + ำ`.
- **Why the space rule is safe.** Thai dependent vowel า never begins a syllable, so a space directly before `า` or `tone+า` is always an artifact. That makes the 2570 space-removal rule linguistically safe.

### 3.3 Word / Office PDF export issues

I found no first-party Microsoft or Adobe statement about Thai ToUnicode defects. Forum reports attribute garbled copy/paste in complex scripts to missing or partial ToUnicode maps ([Adobe community](https://community.adobe.com/t5/acrobat-discussions/pdf-export-to-word-messing-up-lao-and-khmer-text/m-p/15494345)); these are not primary. Our corpus pins the defects to Distiller 7.0 (PUA, missing entries) and Adobe PDF Library 18 (nikhahit → space), not Word.

## 4. Approaches compared

### 4.1 Comparison

| Approach | Accuracy on this corpus | Robust to subsetting / renumbering | Runtime | Maintenance | Status |
|---|---|---|---|---|---|
| A. gid → Unicode table keyed by (family, style, gid), majority-vote built | Fixes every defect in §1.3 at the source, including the 2554 missing entries and 2570 nikhahit; no linguistic rules needed except ำ composition | Valid only while GIDs are preserved (true for all 6 samples, Type0 and TrueType). Guard with an outline hash per glyph so a renumbering producer is detected, not silently misread | `get_texttrace` + dict lookup, roughly the same cost as `get_text_words` (the full 2,894-page scan took about 7 s) | One table per font family (DilleniaUPC R/B); new fonts fall back to B | **Recommended for text pages** (user condition met, §1.2) |
| B. Text-level normalization (PUA `str.translate`, Latin-1 É–Í after Thai → tones, space+า and `ํา` → ำ) | Dict-hit 0.982–0.998 after; residual PUA 0 | Independent of gids; works for any Word/Distiller Thai font | Microseconds per line | Rules grounded in HarfBuzz/Unicode; the Latin-1 rule depends on PyMuPDF's CID flag and on CID = GID tone positions (observed in DilleniaUPC and in `CIDFont+F1/F2`) | **Fallback** for fonts outside the table; the ำ step is needed after A too |
| C. Glyph-outline hashing against a reference font | Same as A once a reference exists | Survives renumbering, which is its only advantage over A | Font parse per subset (cacheable) | Needs the licensed DilleniaUPC TTF (absent here) or a hash table built from the corpus | Use as the **guard** for A, not as the primary mapping |
| D. Tesseract fine-tuned on DilleniaUPC | Unmeasured for Thai. The Impact example went from 2.45% to 0.533% CER after 400 iterations (0.017% on the final eval) with only slight loss on other fonts ([tessdoc 4.00](https://tesseract-ocr.github.io/tessdoc/tess4/TrainingTesseract-4.00.html)) | N/A (pixels) | Same as E | Training pipeline, model artifact, re-evaluation | **Preferred OCR path** if E is not good enough |
| E. Generic Tesseract `tha+eng` 300 dpi | Measured (§5.1): about 1–3% character loss on simple pages, 24–36% on ruled tables; confusables ท/ห, ส/ล, and digit errors | N/A | 0.9 s/page (fast) or 1.5–1.7 s/page (best), 1 core | None | **Baseline OCR** for image pages |
| (rejected) Unicode-level remap without gid guarantee | n/a | n/a | n/a | n/a | rejected (user decision; superseded by A with the uniqueness condition) |

### 4.2 Text-level rules (approach B, exactly as measured)

```python
PUA = {0xF700:0x0E10, 0xF70F:0x0E0D,
       0xF701:0x0E34, 0xF702:0x0E35, 0xF703:0x0E36, 0xF704:0x0E37, 0xF710:0x0E31, 0xF711:0x0E4D, 0xF712:0x0E47,
       0xF713:0x0E48, 0xF714:0x0E49, 0xF715:0x0E4A, 0xF716:0x0E4B, 0xF717:0x0E4C,
       0xF705:0x0E48, 0xF706:0x0E49, 0xF707:0x0E4A, 0xF708:0x0E4B, 0xF709:0x0E4C,
       0xF70A:0x0E48, 0xF70B:0x0E49, 0xF70C:0x0E4A, 0xF70D:0x0E4B, 0xF70E:0x0E4C,
       0xF718:0x0E38, 0xF719:0x0E39, 0xF71A:0x0E3A}           # + Mac F884–F89E if ever seen
t = t.translate(PUA)
t = re.sub(r'(?<=[ก-๏])[É-Í]', lambda m: chr(0x0E48 + ord(m[0]) - 0xC9), t)  # 2554
t = re.sub(r'([ก-ฮ][ั-ฺ]?)\s+([่-๋]?)า', r'\1\2ำ', t)   # 2570
t = re.sub(r'ํ([่-๋]?)า', r'\1ำ', t)                                   # ํ(tone)า → (tone)ำ
t = re.sub(r'([่-๋])ํา', r'\1ำ', t)                                    # (tone)ํา → (tone)ำ
```

The space rule has to run on line text, or across the reader's word join, because `get_text_words` already split at the fake space.

### 4.3 Recommendation for text pages (where it hooks in)

1. **New `words_loader`** (passed to `DocumentText(words_loader=...)`; no change to `_load_page`). It does three things:
   - Iterate `page.get_texttrace()` spans.
   - For spans whose font name's suffix (after `+`) is `DilleniaUPC` or `DilleniaUPCBold`, map each `(style, gid)` through the table. Keep `ucs` for other fonts.
   - Build words from char `bbox`/`origin`: break on mapped spaces (gid 3) and on horizontal gaps.

   Caveats: `chars` are not guaranteed to be ordered within a span; spaces exist only where the producer coded them; gid is "font dependent" ([PyMuPDF get_texttrace](https://pymupdf.readthedocs.io/en/latest/functions.html)). Sort by origin x within a line.
2. **Post-step on every word or line:** the ำ composition rules from §4.2. Run the full approach-B rules only for non-table fonts.
3. **Simplify `fix_pdf_text` / `_join_words`.** Once 206 maps to U+0E4D, the leading-`า` hack becomes dead code for DilleniaUPC. Keep the join for other fonts, and fix the tone-led and mai tri gaps (§1.5).
4. **Guard against renumbering.** Ship a per-(style, gid) outline hash alongside the table. On first sight of a subset (`doc.extract_font(xref)`, cache by xref), hash the gids used on the page and compare. On mismatch, mark the document "gid table not applicable" and fall back to B, then to OCR routing.

   `extract_font` returns `(basename, ext, type, content)`, with an empty buffer for non-embedded fonts ([PyMuPDF Document](https://pymupdf.readthedocs.io/en/latest/document.html)). For Type0 fonts, pass the descendant's xref; PyMuPDF does not document this case.

**Validation plan (text pages):**
- (a) **Coverage:** every DilleniaUPC gid seen in the corpus is in the table. Report unknown gids per document.
- (b) **Before/after counts:** PUA = 0, Latin-1 É–Í after Thai = 0, U+FFFD = 0, space+า = 0, `ํา` = 0.
- (c) **Dictionary hit rate** per page ≥ 0.98, with outliers listed.
- (d) **A/B agreement:** diff the A output against the B output on all pages; any disagreement is a bug in one of them.
- (e) **Reference cmap round trip:** if a licensed `upcdl.ttf`/`upcdb.ttf` becomes available, invert its cmap together with its GSUB-produced PUA glyphs and compare. Not done here, because the font is not installed.
- (f) **Regression:** the existing SUM_MISMATCH / GT fixtures.

## 5. Image pages: OCR comparison

There is a single known font family (DilleniaUPC R/B), Thai plus Arabic/Thai digits, at a few fixed sizes (12.6 and 13.6 pt are dominant in 2558).

### 5.1 (a) Generic Tesseract — measured on our pages

**Setup:**
- Tesseract 5.5.2 (Homebrew), `tha+eng`, models from [tessdata_best](https://github.com/tesseract-ocr/tessdata_best) and [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast). `eng` for fast is the Homebrew copy.
- `OMP_THREAD_LIMIT=1`, Apple M3 Pro.
- 8 random text-heavy 2558 pages rendered at 300 dpi gray, in a clean version and a "scan" version (blur σ 0.8, Gaussian noise σ 12, 0.4° skew, JPEG q55).
- Ground truth: the 2558 text layer (no PUA) with `ํา → ำ` and whitespace removed.

| Variant | Model | psm | CER (order-sensitive) | char-bag error | Thai-only CER | s/page |
|---|---|---|---|---|---|---|
| clean 300 | best | 6 | 0.129 | 0.111 | 0.107 | 1.5 |
| clean 300 | best | 4 | 0.184 | 0.103 | 0.115 | 1.7 |
| clean 300 | fast | 6 | 0.125 | 0.101 | 0.102 | 0.9 |
| scan 300 | best | 6 | 0.132 | 0.127 | 0.115 | 1.7 |
| scan 300 | best | 4 | 0.229 | 0.104 | 0.167 | 1.7 |
| scan 300 | fast | 6 | 0.126 | 0.112 | 0.108 | 1.1 |

**Per page (best, psm 6), the error is bimodal:**
- Pages without ruling: missing 0.3–2.2%, extra 0.2–8%.
- Ruled table pages: 89 (48 drawings) misses 27.5% and 324 (40 drawings) misses 23.8%. Psm 11 does not help (36% and 30%).

**Observed substitutions:** `ทั้งสิ้น → หั้งสิ้น`, `สิ่ง → ลิ่ง`, `2.2 → 22`, `15,775,000 → 16,775,000`.

**Takeaways:**
- The order-sensitive CER is inflated by reading-order differences between my ground-truth line sort and Tesseract's layout. The bag error is a lower bound on true CER.
- Fast and best are equivalent here, and fast is about 1.7× quicker.
- Table ruling, not glyph shape, dominates the error. Remove lines (morphology) or OCR per detected cell before blaming the model. Tesseract's quality guide recommends ≥ 300 dpi and lists the psm modes ([ImproveQuality](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html)).
- **Third-party Thai numbers are unreliable.** The Thai-TrOCR card reports Tesseract CER 0.76 on "PDF Document" and 1.27 overall (104 images) ([thai-trocr](https://huggingface.co/openthaigpt/thai-trocr)). That is inconsistent with our measurement and likely reflects configuration (CER > 1 implies massive insertions), so treat it with caution.

### 5.2 (b) Tesseract fine-tuned on DilleniaUPC (tesstrain)

- **Mechanics.**
  - Line images (`.tif`/`.png`) plus single-line `.gt.txt` go in `data/MODEL-ground-truth`.
  - `START_MODEL=tha` and `TESSDATA` pointing at tessdata_best (fine-tuning requires a float/best model).
  - The learning rate defaults to 0.0001 when fine-tuning, and `MAX_ITERATIONS` defaults to 10000 ([tesstrain README](https://github.com/tesseract-ocr/tesstrain)).
  - The official guidance: fine-tuning suits "a particularly unusual font" and "may work with even a small amount of training data" ([tessdoc 5](https://tesseract-ocr.github.io/tessdoc/tess5/TrainingTesseract-5.html)).
  - The Impact example shows the iteration count must be tuned: "further training beyond 400 iterations makes the error on the base set higher" ([tessdoc 4.00](https://tesseract-ocr.github.io/tessdoc/tess4/TrainingTesseract-4.00.html)).
  - No published Thai single-font fine-tune result was found.
- **Ground truth source 1: synthetic lines from the font.** This needs the full licensed DilleniaUPC TTF to render arbitrary text (text2image or PIL/HarfBuzz). The embedded subsets are partial (only used glyphs) and have no Thai cmap (2550–2562), so they cannot render arbitrary strings without rebuilding a cmap. That is exactly the gid table, which is acceptable only under the verified condition.
- **Ground truth source 2: real line crops from text-layer pages (free, exact, in-domain).**
  - Render each born-digital page and crop each text line by its `rawdict`/texttrace line bbox. The label is the repaired line text from §4.3 A or §4.2 B. Labels must not come from OCR.
  - Pixel/label alignment is exact, because both come from the same drawing operations.
  - Volume is effectively unlimited: about 2,900 sample pages alone give tens of thousands of lines.
  - **How trustworthy the labels are:**
    - After normalization, dictionary hit is 0.982–0.998.
    - The residual is mostly names, abbreviations and out-of-dictionary compounds, not extraction errors. This was not hand-audited; audit about 200 random lines before training.
    - The PUA mapping is a published, lossless table.
    - The sara-am and Latin-1 rules are deterministic and are cross-checked by A/B agreement (§4.3 d).
    - **Known risks:** reading order inside wide table rows (crop per line *segment*, not per page row); Arial digit runs (a different font, so the model sees it, which is fine); hidden or overprinted text (filter span type ≠ 0).
  - **Domain gap:** renders are noise-free. Augment with blur, noise, JPEG, skew and binarization, as in the "scan" variant above, and hold out real scanned pages, once found, for evaluation only.
- **Expected gain:** unknown for Thai. The case for it is that most residual errors in 5.1 are Thai confusables at small UPC x-heights, which a font-specific model targets. Overfitting is controlled by mixing in base `tha` evaluation lines.

### 5.3 (c) Deterministic glyph/template matching

**What makes it feasible:**
- Thai is encoded in visual order for pre-posed vowels (เ แ โ ใ ไ), so no reordering is needed.
- Marks sit in four vertical zones (MS classes ABOVE1–4, BELOW1–2).
- Sara am is two components (nikhahit + aa), which recompose to ำ.
- Templates exist: the embedded subsets contain outlines for every glyph actually used. Render them at the page's point sizes.

**Why it is not the main path:**
- Connected components break under scan noise: tight UPC spacing makes glyphs touch, and thin strokes break.
- The small marks (่ ้ ๊ ๋ ์ ิ ี) differ by a few pixels at 12–14 pt and 300 dpi.
- No primary source reports Thai template OCR accuracy.

**Where it is worth doing: pages where text was converted to vector outlines.** There, match `page.get_drawings()` glyph paths against the corpus outline hashes (exact, deterministic, no pixels). None of the six samples contains such pages, so this is unevaluated.

### 5.4 (d) Open Thai OCR models

| Model | Published numbers (primary source) | CPU cost | Notes |
|---|---|---|---|
| Typhoon OCR 3B/7B, v1.5 2B (SCB10X; Qwen2.5-VL / Qwen3-VL) | Thai Government Forms Levenshtein 0.04–0.08 (v1), 0.035 (v1.5 2B); Financial Reports 0.07–0.08. Normalization is not stated ([arXiv 2601.14722](https://arxiv.org/html/2601.14722)) | GPU required per the model card; "specific prompt only"; GGUF builds "may suffer from accuracy issues" ([HF card](https://huggingface.co/scb10x/typhoon-ocr1.5-2b)) | Best published Thai document numbers; generative (hallucination risk on numbers); seconds per page on GPU (unmeasured) |
| PaddleOCR `th_PP-OCRv5_mobile_rec` | 82.68% recognition accuracy on an unspecified Thai set ([PaddleOCR docs](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html)) | CPU feasible (mobile model; unmeasured) | Line-level accuracy metric, not CER |
| EasyOCR (Thai) | CER 0.086 "PDF Document" / 0.29 real documents, from Thai-TrOCR authors' 104-image test ([thai-trocr](https://huggingface.co/openthaigpt/thai-trocr)); no first-party EasyOCR Thai benchmark | CPU slow (unmeasured) | Thai support not confirmed from the README text fetched |
| Thai-TrOCR (OpenThaiGPT, 0.1B) | CER 0.058 PDF documents, 0.124 mean (same 104 images) | CPU feasible (unmeasured) | Line recognizer; needs a separate detector |

All of these must be run through the same harness (§5.5) before any choice is made. None of the published numbers is on DilleniaUPC budget tables.

### 5.5 How to measure CER on our corpus

1. Pick N born-digital pages per year, stratified by layout (prose vs ruled table).
2. Ground truth: repaired text layer (A, cross-checked with B), per line, from texttrace line bboxes.
3. Render at 300 dpi, and at 200/400 dpi for sensitivity, in clean and degraded versions. Keep the degradation parameters fixed and versioned.
4. OCR with each candidate. Align at line level: match OCR lines to ground-truth lines by bbox overlap (Tesseract TSV/hOCR gives boxes) so reading order does not pollute CER.
5. Report CER (Levenshtein / ground-truth length) on NFC text with `ํา → ำ`. Report separately:
   - Thai letters
   - marks (tones, above/below vowels)
   - digits

   Digit CER and amount-level exact match matter most for the budget tables; also run the parser's SUM checks.
6. When real scanned pages turn up, hand-transcribe about 20 lines per volume as the only non-synthetic test set.

## 6. Routing and parallel OCR

**Per-page routing** (cheap checks first):

| Signal | Action |
|---|---|
| No text chars, or image area covers more than about 50% of the page, or many drawings with little text (outlined glyphs) | OCR (or outline matching, §5.3) |
| Every Thai span is in a table font (DilleniaUPC R/B) and the outline-hash guard passes | Approach A |
| Other fonts, or the guard fails | Approach B |
| After A/B: U+FFFD, PUA or Latin-1-after-Thai remaining, or dictionary hit < 0.90 | OCR that page; log it |

To find unknown codes, re-extract with `flags=TEXTFLAGS_WORDS & ~TEXT_USE_CID_FOR_UNKNOWN_UNICODE` and look for U+FFFD; PyMuPDF documents this toggle for detection ([vars](https://pymupdf.readthedocs.io/en/latest/vars.html)).

**Bounded parallelism:**
- **Process model.** Run one single-threaded Tesseract process per core with `OMP_THREAD_LIMIT=1`. The Tesseract FAQ: "Using a single thread … is also the best solution for processing lots of images by running one Tesseract process per CPU core"; "To disable multithreading, use `OMP_THREAD_LIMIT=1`" ([FAQ](https://tesseract-ocr.github.io/tessdoc/FAQ.html)).
- **Memory.** OCRmyPDF budgets "about 15 bytes per pixel of the largest page, per concurrent job"; "Tesseract peaks at about 12 bytes per pixel" ([OCRmyPDF performance](https://ocrmypdf.readthedocs.io/en/latest/performance.html)). An A4 page at 300 dpi gray is about 8.7 Mpx, so roughly 105–130 MB per worker; 11 workers is about 1.5 GB.
- **Implementation.** A `ProcessPoolExecutor(max_workers=os.cpu_count())` that renders one page per task inside the worker (never pre-render a whole volume). Throughput is about 0.9–1.7 s per page per core, so 11 cores give about 6–12 pages/s.

## Sources

- ISO 32000-1:2008 (Adobe copy): https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf — §9.6.4 Font Subsets, §9.6.6.4, Table 117 CIDToGIDMap, §9.10.2
- MuPDF: https://github.com/ArtifexSoftware/mupdf/blob/master/source/pdf/pdf-unicode.c , https://github.com/ArtifexSoftware/mupdf/blob/master/source/pdf/pdf-op-run.c , https://github.com/ArtifexSoftware/mupdf/blob/master/source/pdf/pdf-font.c
- pdf.js: https://github.com/mozilla/pdf.js/blob/master/src/core/evaluator.js
- PDFBox: https://github.com/apache/pdfbox/blob/trunk/pdfbox/src/main/java/org/apache/pdfbox/pdmodel/font/PDType0Font.java , .../PDFont.java
- poppler: https://gitlab.freedesktop.org/poppler/poppler/-/blob/master/poppler/GfxFont.cc
- HarfBuzz Thai PUA tables: https://github.com/harfbuzz/harfbuzz/blob/main/src/hb-ot-shaper-thai.cc
- UnicodeData.txt: https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt
- Unicode 18.0 §16.1 Thai: https://www.unicode.org/versions/Unicode18.0.0/core-spec/chapter-16/
- UAX #15 rev 58: https://www.unicode.org/reports/tr15/tr15-58.html
- Microsoft, Developing OpenType Fonts for Thai Script: https://learn.microsoft.com/en-us/typography/script-development/thai
- Microsoft, DilleniaUPC font family: https://learn.microsoft.com/en-us/typography/font-list/dilleniaupc
- PyMuPDF: https://pymupdf.readthedocs.io/en/latest/functions.html (get_texttrace), https://pymupdf.readthedocs.io/en/latest/document.html (extract_font), https://pymupdf.readthedocs.io/en/latest/vars.html (text flags)
- fontTools RecordingPen: https://fonttools.readthedocs.io/en/latest/pens/recordingPen.html
- Tesseract: https://tesseract-ocr.github.io/tessdoc/tess4/TrainingTesseract-4.00.html , https://tesseract-ocr.github.io/tessdoc/tess5/TrainingTesseract-5.html , https://github.com/tesseract-ocr/tesstrain , https://tesseract-ocr.github.io/tessdoc/FAQ.html , https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html , https://github.com/tesseract-ocr/tessdata_best , https://github.com/tesseract-ocr/tessdata_fast
- OCRmyPDF performance: https://ocrmypdf.readthedocs.io/en/latest/performance.html
- Typhoon OCR: https://arxiv.org/html/2601.14722 , https://huggingface.co/scb10x/typhoon-ocr1.5-2b
- PaddleOCR PP-OCRv5 multilingual: https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html
- Thai-TrOCR (contains EasyOCR/Tesseract comparison): https://huggingface.co/openthaigpt/thai-trocr
- EasyOCR: https://github.com/JaidedAI/EasyOCR

**Not verified:**
- Whether Distiller / Adobe PDF Library guarantee GID preservation (observed only).
- The meaning of DilleniaUPC's 224 vs 362 glyph counts (font version, inferred).
- The Typhoon Levenshtein normalization.
- EasyOCR Thai CER from a first-party source.
- CPU cost of PaddleOCR, EasyOCR and Thai-TrOCR.
- Any Thai single-font Tesseract fine-tune result.
