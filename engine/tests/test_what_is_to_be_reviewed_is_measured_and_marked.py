"""What the reading cannot settle is measured all the same, and marked to be reviewed.

A run two labels name differently used to stand outside the takeoff ("pointed at but unnamed"), and pipe drawn
on a pipe pen that no label reached was a grey line and a figure in a footnote. Both are now measured: the run
in doubt under the name the sheet's labels support most - counted, marked, with the other candidates written
on it - and the unnamed run as "Onämnt rör" on its pen, shown and marked but kept out of the confirmed figure.
A pen that is mostly background - almost none of its ink named - gives no unnamed rows.
"""
import pymupdf

from vvs_engine import rules
from vvs_engine.pdf.extract import extract_document
from vvs_engine.pipeline import analyze_page

PEN, LEAD = 0.72, 0.24


def _label(page, x, y, text, to):
    page.insert_text((x, y), text, fontsize=9, fontname="helv")
    page.draw_line((x, y + 3), (x + 62, y + 3), width=LEAD, color=(0, 0, 0))
    page.draw_line((x + 62, y + 3), to, width=LEAD, color=(0, 0, 0))
    page.draw_line((to[0] - 2, to[1] + 2), (to[0] + 2, to[1] - 2), width=LEAD, color=(0, 0, 0))


def _sheet(path, doubt=False, loose=False):
    doc = pymupdf.open()
    page = doc.new_page(width=1191, height=842)
    kb = doc.add_ocg("v50_p260|V-55512")
    vs = doc.add_ocg("v50_p260|V-56512")
    page.draw_line((100, 300), (700, 300), width=PEN, color=(0, 0, 0), oc=kb)
    page.draw_line((100, 450), (700, 450), width=PEN, color=(0, 0, 0), oc=vs)
    for x in (110.0, 260.0, 410.0):
        _label(page, x, 250.0, "KB02-3-35", (x + 70, 300.0))
    for x in (110.0, 260.0, 410.0):
        _label(page, x, 400.0, "VS02-22-15", (x + 70, 450.0))
    if doubt:
        # a second run of the cooling pen whose labels all end on one spot: two name it one thing, one another
        page.draw_line((100, 600), (500, 600), width=PEN, color=(0, 0, 0), oc=kb)
        for x, y, t in ((110.0, 520.0, "KB02-3-28"), (230.0, 520.0, "KB02-3-28"), (350.0, 540.0, "KB02-3-42")):
            _label(page, x, y, t, (300.0, 600.0))
    if loose:
        page.draw_line((800, 300), (1000, 300), width=PEN, color=(0, 0, 0), oc=kb)   # nobody names it
    page.insert_text((100, 800), "SKALA 1:100", fontsize=10, fontname="helv")
    doc.save(path)
    doc.close()
    return path


def _read(path, overrides=None):
    with rules.using(overrides):
        pa = analyze_page(extract_document(path).pages[0])
    return {q["designation"]: q for q in pa.quantities}, pa


def test_an_unnamed_run_on_a_pipe_pen_is_a_row_to_review(tmp_path):
    rows, pa = _read(_sheet(str(tmp_path / "loose.pdf"), loose=True))
    unnamed = [r for k, r in rows.items() if k.startswith("Onämnt rör")]
    assert len(unnamed) == 1 and unnamed[0]["state"] == "UNNAMED", rows
    assert 6.5 < unnamed[0]["unnamed_review_m"] < 7.6 and unnamed[0]["confirmed_total_m"] == 0, unnamed
    assert any(p.needs_review and p.identity.display.startswith("Onämnt rör") for p in (pa.ownership.pipes + pa.ownership.review_pipes))
    clean, _ = _read(_sheet(str(tmp_path / "clean.pdf")))
    assert rows["KB02-3-35"]["confirmed_total_m"] == clean["KB02-3-35"]["confirmed_total_m"]


def test_with_the_rule_off_the_unnamed_run_is_no_row(tmp_path):
    rows, _ = _read(_sheet(str(tmp_path / "loose.pdf"), loose=True), {"pipes.ownership.UNNAMED_RUNS_ARE_ROWS": False})
    assert not any(k.startswith("Onämnt rör") for k in rows), rows


def test_a_pen_mostly_unnamed_gives_no_unnamed_rows(tmp_path):
    rows, _ = _read(_sheet(str(tmp_path / "loose.pdf"), loose=True), {"pipes.ownership.UNNAMED_PEN_NAMED_SHARE": 0.9})
    assert not any(k.startswith("Onämnt rör") for k in rows), rows


def test_a_run_in_doubt_is_measured_under_its_best_reading_and_marked(tmp_path):
    rows, pa = _read(_sheet(str(tmp_path / "doubt.pdf"), doubt=True))
    doubt = [p for p in (pa.ownership.pipes + pa.ownership.review_pipes) if "best_reading_among_candidates" in p.evidence]
    assert doubt, {k: (r["confirmed_total_m"], r["ambiguous_m"]) for k, r in rows.items()}
    assert all(p.needs_review for p in doubt)
    assert {p.identity.display for p in doubt} == {"KB02-3-28"}, [p.identity.display for p in doubt]
    assert rows["KB02-3-28"]["proposed_review_m"] > 5, rows["KB02-3-28"]
    assert rows["KB02-3-28"]["confirmed_total_m"] == 0, rows["KB02-3-28"]      # proposed, not confirmed


def test_with_the_rule_off_the_run_in_doubt_stays_out(tmp_path):
    _, pa = _read(_sheet(str(tmp_path / "doubt.pdf"), doubt=True),
                  {"pipes.ownership.BEST_READING_AMONG_CANDIDATES": False})
    assert not any("best_reading_among_candidates" in p.evidence for p in (pa.ownership.pipes + pa.ownership.review_pipes))
