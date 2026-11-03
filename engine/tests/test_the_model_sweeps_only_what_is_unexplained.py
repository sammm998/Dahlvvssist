"""Med en modell vald ser den hela bladet inzoomat – men bara där något fortfarande är oförklarat, och aldrig samma
del två gånger. Ett blad där allt är förklarat kostar inget extra.

Svepet visar modellen de delar av bladet där ett onämnt rör eller en etikett utan rör står kvar och som ingen
fråga visat den inzoomat, högst SWEEP_MAX_TILES rutor. Den svarar bara med beteckningar den ser där och som
läsningen inte läste. En sådan beteckning erbjuds de onämnda rören vid den, bara om bladet själv skriver samma
beteckning med en dimension någon annanstans; det modellen namnger så står som att granska. Det som inte stämmer
redovisas som sett, inte läst.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))

from app.drawing_evidence import CELL, DETAIL_TILES
from app.source_model import AssignmentTransport
from vvs_engine.source_rules import completeness_check
from vvs_engine.source_rules.pipestudio import final_bind


class Ask:
    """A stand-in for the model: names what it is asked with the first candidate, and reports from the sweep
    whatever it is told to."""
    def __init__(self, seen=()):
        self.seen, self.swept, self.asked = list(seen), [], []

    def __call__(self, qs):
        self.asked.extend(q['stretch'] for q in qs)
        return [{'stretch': q['stretch'], 'label': q['candidates'][0]['label'] if q['candidates'] else None,
                 'designation_idx': 0 if q['candidates'] else None, 'ambiguous': False} for q in qs]

    def sweep(self, places, read, max_tiles):
        self.swept.append((list(places), max_tiles))
        return list(self.seen), 1


def _questions(monkeypatch):
    monkeypatch.setattr(final_bind, 'questions',
                        lambda A, R, L: [{'stretch': s['id'], 'candidates': []} for s in A['stretches']])


L = [{'id': 0, 'rect': [0, -30, 60, -10], 'text': 'KV1-K1-22', 'designations': [{'raw': 'KV1-K1-22', 'dimension': 22}]}]


def test_a_sheet_with_nothing_unexplained_is_not_swept(monkeypatch):
    _questions(monkeypatch)
    A = {'stretches': [{'id': 1, 'points': [[0, 0], [100, 0]], 'length': 100}]}
    bindings = [{'id': 0, 'stretch': 1, 'label': 0, 'designation_idx': 0, 'confidence': 'high', 'rule': 'astra_final'}]
    ask = Ask()
    report = completeness_check.check(A, {'bindings': []}, L, {'combined': {'result': {'bindings': bindings}}},
                                      ask, 'test-model')
    assert ask.swept == [] and report['swept_tiles'] == 0 and ask.asked == []


def test_a_label_the_model_sees_where_the_reading_read_none_is_offered_to_the_pipe_there(monkeypatch):
    _questions(monkeypatch)
    # stretch 2 lies far from every label: no question reaches it, so only the sweep can see what names it
    A = {'stretches': [{'id': 1, 'points': [[0, 0], [100, 0]], 'length': 100},
                       {'id': 2, 'points': [[20, 1000], [200, 1000]], 'length': 180}]}
    bindings = [{'id': 0, 'stretch': 1, 'label': 0, 'designation_idx': 0, 'confidence': 'high', 'rule': 'astra_final'}]
    result = {'combined': {'result': {'bindings': bindings}}}
    cell = [0, int(1000 // CELL)]
    ask = Ask(seen=[{'text': 'KV1-K1-22', 'cell': cell}, {'text': 'XY9-Q1-99', 'cell': cell}])
    report = completeness_check.check(A, {'bindings': []}, L, result, ask, 'test-model')
    places, cap = ask.swept[0]
    assert (20, 1000) in places and cap == completeness_check.SWEEP_MAX_TILES
    added = result['combined']['result']['bindings'][-1]
    assert (added['stretch'], added['label'], added['confidence'], added['rule']) == (2, 0, 'low', 'model_sweep')
    assert report['sweep_named'] == 1
    # a designation the sheet writes nowhere else is never proposed: it is reported as seen, not read
    assert report['seen_not_read'] == [{'text': 'XY9-Q1-99', 'cell': cell}]


def test_the_sweep_can_be_turned_off(monkeypatch):
    _questions(monkeypatch)
    monkeypatch.setenv('VVS_SHEET_SWEEP', '0')
    A = {'stretches': [{'id': 2, 'points': [[20, 1000], [200, 1000]], 'length': 180}]}
    ask = Ask(seen=[{'text': 'KV1-K1-22', 'cell': [0, 3]}])
    completeness_check.check(A, {'bindings': []}, L, {'combined': {'result': {'bindings': []}}}, ask, 'test-model')
    assert ask.swept == []


def _sheet(tmp_path, size=2400):
    path = tmp_path / 'sheet.pdf'
    doc = pymupdf.open()
    page = doc.new_page(width=size, height=size)
    for i in range(0, size, 200):
        page.draw_line((i, 10), (i, size - 10), color=(0, 0, 0), width=1)
    doc.save(path)
    doc.close()
    return path


def test_the_transport_never_shows_a_part_twice_and_keeps_to_its_cap(tmp_path):
    path = _sheet(tmp_path)
    sent = []

    def create(**kw):
        sent.append(kw)
        key = 'decisions' if kw['text']['format']['name'] == 'pipe_assignments' else kw['text']['format']['name']
        return NS(status='completed', output_text=json.dumps({key: []}), usage=None, model='test', id=f'r{len(sent)}')
    t = AssignmentTransport(NS(responses=NS(create=create)), 'test')
    t = t.for_page(NS(source_path=str(path), info=NS(index=0))).with_places({}).for_style({'rules': []})
    # a question shows the cell at the sheet's corner up close
    t([{'stretch': 1, 'points': [[20, 20], [60, 20]], 'candidates': []}])
    assert len(sent) == 1
    # the sweep is handed something unexplained in that cell and in twenty others
    places = [(20, 30)] + [((k % 7) * CELL + 50, (k // 7 + 1) * CELL + 50) for k in range(20)]
    seen, tiles = t.sweep(places, [], 12)
    assert seen == [] and tiles == 12
    sweeps = [kw for kw in sent if kw['text']['format']['name'] == 'seen']
    assert len(sweeps) == -(-12 // DETAIL_TILES)
    shown = [tuple(a['cell']) for u in t.usage if u.get('purpose') == 'sheet_sweep'
             for a in u['drawing_images'] if a.get('cell')]
    assert (0, 0) not in shown and len(shown) == len(set(shown)) == 12
    # asked again, it shows only what it has not shown yet
    seen, tiles = t.sweep(places, [], 12)
    assert tiles == 8
    seen, tiles = t.sweep(places, [], 12)
    assert tiles == 0 and len([kw for kw in sent if kw['text']['format']['name'] == 'seen']) == 4
