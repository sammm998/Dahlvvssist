"""A model reading a sheet is shown every pipe it is asked about, the labels that may name it and both ends of their
leaders in a zoomed detail crop - not only as the whole-sheet overview, where a 2 mm label is a smudge.

A request carries the overview and at most DETAIL_TILES crops. Questions spread over more of the sheet than that are
asked in consecutive requests, each with its own crops; nothing is left to the overview alone."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))

from app.drawing_evidence import CELL, DETAIL_TILES
from app.source_model import AssignmentTransport
from vvs_engine.source_rules.native_assignment import label_places


def _sheet(tmp_path, size=2400):
    path = tmp_path / 'sheet.pdf'
    doc = pymupdf.open()
    page = doc.new_page(width=size, height=size)
    for i in range(0, size, 200):
        page.draw_line((i, 10), (i, size - 10), color=(0, 0, 0), width=1)
    doc.save(path)
    doc.close()
    return path


def _covered(rect, p):
    return rect[0] <= p[0] <= rect[2] and rect[1] <= p[1] <= rect[3]


def _transport(path, places):
    sent = []

    def create(**kw):
        sent.append(kw)
        return NS(status='completed', output_text='{"decisions":[]}', usage=None, model='test', id=f'r{len(sent)}')
    t = AssignmentTransport(NS(responses=NS(create=create)), 'test')
    t = t.for_page(NS(source_path=str(path), info=NS(index=0))).with_places(places).for_style({'rules': []})
    return t, sent


def test_the_label_and_the_leader_ends_are_zoomed_in_with_the_pipe(tmp_path):
    path = _sheet(tmp_path)
    # the pipe lies in one corner, its label two cells away, and the leader runs from the label to the pipe
    L = [{'id': 7, 'rect': [1500, 1490, 1580, 1510]}]
    R = {'leaders': [{'label': 7, 'points': [[1500, 1500], [1100, 1300], [700, 700]]}]}
    places = label_places(L, R)
    assert sorted(places[7]) == sorted([(1500, 1500.0), (1580, 1500.0), (1500, 1500), (700, 700)])
    t, sent = _transport(path, places)
    t([{'stretch': 1, 'points': [[600, 650], [760, 650]], 'candidates': [{'label': 7, 'designation_idx': 0, 'text': 'V1-25',
                                                                     'designation': {'raw': 'V1-25'}, 'evidence': []}]}])
    assert len(sent) == 1
    rects = [a['rect'] for a in t.usage[0]['drawing_images'] if a['kind'] == 'detail']
    for p in [(600, 650), (760, 650), (1500, 1500), (1580, 1500), (700, 700)]:
        assert any(_covered(r, p) for r in rects), p


def test_questions_spread_over_the_sheet_are_split_so_none_is_left_to_the_overview(tmp_path):
    path = _sheet(tmp_path)
    # twenty pipes, each in its own cell of the sheet: more than one request's worth of crops
    qs = [{'stretch': i, 'points': [[(i % 6) * 400 + 20, (i // 6) * 400 + 20], [(i % 6) * 400 + 60, (i // 6) * 400 + 20]],
           'candidates': []} for i in range(20)]
    t, sent = _transport(path, {})
    assert t(qs) == []
    assert len(sent) == len(t.usage) >= -(-20 // DETAIL_TILES)
    assert sum(u['questions'] for u in t.usage) == 20
    asked = 0
    for u in t.usage:
        rects = [a['rect'] for a in u['drawing_images'] if a['kind'] == 'detail']
        assert len(rects) <= DETAIL_TILES
        mine = qs[asked:asked + u['questions']]
        asked += u['questions']
        for q in mine:
            for p in q['points']:
                assert any(_covered(r, p) for r in rects), (q['stretch'], p)
    # every request still opens with the same overview, the part the provider caches
    overviews = [kw['input'][1]['content'] for kw in sent]
    assert all(o == overviews[0] for o in overviews)


def test_questions_close_together_still_go_in_one_request(tmp_path):
    path = _sheet(tmp_path)
    qs = [{'stretch': i, 'points': [[20 + i * 10, 20], [40 + i * 10, 20]], 'candidates': []} for i in range(12)]
    t, sent = _transport(path, {})
    t(qs)
    assert len(sent) == 1 and t.usage[0]['questions'] == 12
    assert CELL == 320
