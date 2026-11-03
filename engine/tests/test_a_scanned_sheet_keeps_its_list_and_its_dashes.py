"""Två fel som syntes på inskannade blad, rättade allmänt.

Förklaringslistan slutar där den slutar. Samma vänsterkant löper ofta vidare ned i namnrutan - konsultlistan,
`V VVS-KONSULT AB`, `E ELKONSULT AB` - och läst som mer av listan blev en konsults initial en systemkod: `V`
öppnade bladets eget nummer `V50-02-421`, som mättes som ett rör namnrutan lång. Ett hopp mellan listans poster
på mer än LIST_BREAK_ROWS postavstånd avslutar ett block, och listan är det största blocket. Listans egna
avsnitt, några rader isär, står kvar.

Ett streckmönster känns igen fast pixlarna flyttar glappen. På en inskannad plan vars rör alla är streck-prick
lästes samma glapp som 8,75, 9,0 och 9,25 pt i nästan lika delar; ingen enskild storlek nådde den andel ett
mönster kräver, inget streck fogades till nästa och bladet mätte 24 m av 2 300. På en sida läst ur bild räknas
glapp inom en halv punkt som samma glapp. En vektorsida, vars glapp är exakta, räknas som förut.
"""
from collections import Counter

from vvs_engine.pipes.representation import RASTER_TOL, VECTOR_TOL, _windowed_modes
from vvs_engine.semantics.legend import read_legend
from vvs_engine.text.model import Glyph, make_row


def _row(text, x, y, h=6.0):
    w = 0.6 * h
    glyphs = [Glyph(gid=f"{x}-{y}-{i}", char=c, bbox=(x + i * w, y, x + (i + 1) * w, y + h), source="text")
              for i, c in enumerate(text)]
    return make_row(0, glyphs, 0.0, "text")


def _list_then_title_block():
    rows, y = [], 100.0
    rows.append(_row("SYSTEM", 100, y)); y += 10
    for code, desc in [("KV1", "KALLVATTEN"), ("VV1", "VARMVATTEN"), ("VVC1", "VARMVATTENCIRKULATION"),
                       ("S1", "SPILLVATTEN"), ("D1", "DAGVATTEN"), ("VS1", "VARMEVATTEN")]:
        rows += [_row(code, 100, y), _row(desc, 140, y)]; y += 10
    y += 40                                      # a section a few lines further down: still the list
    rows.append(_row("VENTILER", 100, y)); y += 10
    for code, desc in [("AV", "AVSTANGNINGSVENTIL"), ("RV", "REGLERVENTIL"), ("SV", "STYRVENTIL")]:
        rows += [_row(code, 100, y), _row(desc, 140, y)]; y += 10
    y += 400                                     # the title block, far below on the same edge
    for code, desc in [("A", "ARKITEKT AB"), ("C", "KONSTRUKTÖR AB"), ("E", "ELKONSULT AB"), ("V", "VVS-KONSULT AB")]:
        rows += [_row(code, 100, y), _row(desc, 140, y)]; y += 14
    return rows


def test_the_list_ends_before_the_title_block_and_keeps_its_own_sections():
    lg = read_legend(_list_then_title_block())
    codes = [e.code for e in lg.entries]
    assert codes[:6] == ["KV1", "VV1", "VVC1", "S1", "D1", "VS1"]
    assert {"AV", "RV", "SV"} <= set(codes), "a section of the list a few lines down is the list"
    assert not {"A", "C", "E", "V"} & set(codes), "the consultants in the title block are not codes"


def test_a_scanned_dash_pattern_is_found_though_pixels_spread_its_gap():
    # one 9 pt gap read a pixel either way, plus the scatter of other ink in the same pen
    gaps = [8.75] * 143 + [9.0] * 190 + [9.25] * 177 + [round(2 + 0.25 * i, 2) for i in range(60)] * 18
    hist = Counter(round(g * 4) / 4 for g in gaps)
    assert all(k < 0.15 * len(gaps) for k in hist.values()), "no single bin carries the pattern"
    modes = _windowed_modes(hist, len(gaps), RASTER_TOL.gap_window)
    assert modes and abs(modes[0] - 9.0) <= 0.25
    assert all(abs(m - modes[0]) > 2 * RASTER_TOL.gap_window for m in modes[1:])
    assert VECTOR_TOL.gap_window == 0, "an exported sheet's gaps are exact and are counted as before"
