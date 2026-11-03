"""Allt en förklaringslista skriver ska läsas: varje rad för sig, varje ord helt, och varje kod som det listans
egen rubrik säger att den är.

Tre sätt en lista tappade sina rader på, alla allmänna:

  * Två rader satta tätt hölls ihop av en liten bit mellan dem - ett kommatecken vid den övre radens fot, ett
    löst tvärstreck i ett E eller T i den nedre radens topp - och lästes som en rad frågetecken. Koden bredvid
    blev då utan beskrivning och togs för en rubrik: en lista tappade tre ventilkoder, två klosettkoder och ett
    av sina system så.
  * Ringen i ett Å, läst för sig som `O`, ersatte hela ordet den låg i (`PÅFYLLNINGSVENTIL`), som om de vore
    samma text ritad två gånger.
  * Rubriken över ett avsnitt säger vad koderna under den är - SYSTEM, MATERIAL, ISOLERINGTYP - och lästes inte.
"""
from types import SimpleNamespace

from vvs_engine.semantics.annotation import one_reading_per_place
from vvs_engine.semantics.legend import DrawingLegend, LegendEntry, assign_roles, role_from_heading
from vvs_engine.text.model import Glyph, make_row
from vvs_engine.text.strokes import StrokeComponent, _split_and_order


def _stroke(i, x0, y0, x1, y1):
    seg = SimpleNamespace(x0=x0, y0=y0, x1=x1, y1=y1)
    return StrokeComponent(cid=f"c{i:03d}", layer="0", style="s", paths=[], segs=[seg], bbox=(x0, y0, x1, y1), kind="s")


def test_two_lines_set_close_stay_two_lines_with_a_comma_and_loose_bars_between_them():
    """Two legend lines a third of a letter apart, laid out as they were measured on a real sheet (H = 6.25 pt):
    full-height strokes on each line, the loose cross-bars of its letters, and a comma at the foot of the first
    line above a letter of the second. Read as runs of positions, the bars and the comma tied the lines together."""
    H = 6.25
    cs, i = [], 0
    for line, top in ((0, 100.0), (1, 109.5)):
        for k in range(16):
            x = 100.0 + 5.7 * k
            cs.append(_stroke(i, x, top, x, top + 6.4)); i += 1
            cs.append(_stroke(i, x + 3.5, top, x + 3.5, top + 6.4)); i += 1
    for x in (106.0, 140.0, 175.0):
        cs.append(_stroke(i, x, 104.7, x + 3.0, 104.7)); i += 1          # bars low on the first line
        cs.append(_stroke(i, x + 10, 109.5, x + 13.5, 109.5)); i += 1    # bars at the head of the second
    cs.append(_stroke(i, 187.0, 106.4, 186.6, 107.8))                    # the comma
    page = SimpleNamespace(info=SimpleNamespace(index=0))
    rows = _split_and_order(page, cs, H, 0.0)
    assert len(rows) == 2, [(len(r.glyphs), round(r.height, 1)) for r in rows]
    assert all(r.height <= 1.3 * H for r in rows)
    top, low = sorted(rows, key=lambda r: r.glyphs[0].bbox[1])
    # the comma stays with the line it closes
    assert any(g.bbox[3] >= 107.7 for g in top.glyphs) and all(g.bbox[1] >= 109.4 for g in low.glyphs)


def _row(text, bbox):
    w = (bbox[2] - bbox[0]) / max(len(text), 1)
    glyphs = [Glyph(gid=f"g{i}", char=c, bbox=(bbox[0] + i * w, bbox[1], bbox[0] + (i + 1) * w, bbox[3]),
                    source="stroke", score=1.0 if len(text) == 1 else 0.8) for i, c in enumerate(text)]
    return make_row(0, glyphs, 0.0, "stroke")


def test_the_ring_of_an_a_read_alone_does_not_replace_the_word_it_sits_in():
    word = _row("PÅFYLLNINGSVENTIL", (100.0, 100.0, 186.0, 109.3))
    ring = _row("O", (107.0, 100.0, 108.8, 101.8))
    kept = one_reading_per_place([word, ring])
    assert [r.text for r in kept] == ["PÅFYLLNINGSVENTIL"]
    # the same label read twice is still read once, the better reading kept
    twice = one_reading_per_place([_row("KV1-15", (10, 10, 40, 16)), _row("KV1-15", (10.2, 10.1, 40.1, 16.1))])
    assert len(twice) == 1


def _entry(code, description, heading, y):
    return LegendEntry(code=code, description=description, heading=heading, bbox=(0.0, y, 10.0, y + 5.0))


def test_the_title_of_a_section_says_what_its_codes_are():
    assert role_from_heading("SYSTEM") == "system"
    assert role_from_heading("MATERIAL") == "material"
    assert role_from_heading("ISOLERINGTYP") == "material"
    assert role_from_heading("APPARATER") is None and role_from_heading("") is None
    legend = DrawingLegend(entries=[
        _entry("KV1", "TAPPKALLVAT TEN", "SYSTEM", 0),          # a description the lettering split
        _entry("VS1", "VÄRMEVATTEN", "SYSTEM", 10),
        _entry("S1", "SPILLVATTEN", "SYSTEM", 20),
        _entry("K1", "KOPPARRÖR", "MATERIAL", 30),
        _entry("S1", "KÖLDBÄRARE", "ISOLERINGTYP", 40),
        _entry("S2", "KALLVATTEN", "ISOLERINGTYP", 50),          # insulation for cold water, not a system
        _entry("B1XX", "GOLVBRUNN", "APPARATER", 60),
    ])
    assign_roles(legend, [])
    roles = [(e.code, e.role) for e in legend.entries]
    assert roles == [("KV1", "system"), ("VS1", "system"), ("S1", "system"), ("K1", "material"),
                     ("S1", "material"), ("S2", "material"), ("B1XX", "component")]
    assert {e.role_from for e in legend.entries[:6]} == {"the_list_heading_says_so"}
    # a code written in two sections opens a pipe when one of them makes it a system
    assert legend.role_of_head("S1-P3-110") == "system"
    assert legend.role_of_head("S2") == "material"
