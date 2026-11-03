"""Ett rör slutar inte där nästa mätsektion av samma rör börjar.

Den inbyggda läsaren delar ett rör i sektioner vid varje nod den sätter, så att en höjd kan knytas till rätt bit.
Rapporten över var rören slutar räknade varje sådan skarv som en kant, "något läsningen inte kan sätta ord på" -
tolv tusen av korpusens femton tusen rörändar - och de verkliga ändarna, där röret möter en ventil, en stigare
eller ett annat system, drunknade bland dem. En skarv där samma rör med samma namn fortsätter är ingen ände; en
sektion vars båda ändar är skarvar är ändå redovisad, och läsningen blir inte ogiltig för den.
"""
from types import SimpleNamespace as NS

from vvs_engine.pipes.frontier import (REAL_SYSTEM_BOUNDARY, SECTION_JOINT, UNSUPPORTED_STRUCTURE, frontiers_of,
                                       summary)
from vvs_engine.pipes.ownership import Identity, PrimState


def _graph():
    # A - B - C - D in one pen: three sections of one cold water run, a heating pipe beyond each end
    xs = {"A": 0, "B": 100, "C": 200, "D": 300}
    order = ["A", "B", "C", "D"]
    prims = {0: ("A", "B"), 1: ("B", "C"), 2: ("C", "D"), 3: ("A", "A2"), 4: ("D", "D2")}
    nodes = {}
    for nid, x in list(xs.items()) + [("A2", -50), ("D2", 350)]:
        on = [p for p, ends in prims.items() if nid in ends]
        nodes[nid] = NS(nid=nid, x=float(x), y=0.0, prims=on, degree=len(on))
    g = NS(nodes=nodes, prims={p: NS(seg=NS(length=100.0)) for p in prims}, prim_nodes=prims)
    return g, order


def test_a_joint_between_two_sections_of_one_pipe_is_not_an_end():
    g, _ = _graph()
    kv = Identity(base="KV1-K1", dn=22, system="KV1", display="KV1-K1-22")
    vs = Identity(base="VS1-S13", dn=15, system="VS1", display="VS1-S13-15")
    st = {p: PrimState(state="CONFIRMED", identity=kv, reason="native") for p in (0, 1, 2)}
    st.update({3: PrimState(state="CONFIRMED", identity=vs, reason="native"),
               4: PrimState(state="CONFIRMED", identity=vs, reason="native")})
    pipes = [NS(physical_pipe_id=f"pp{p}", family="f", identity=kv, prim_ids=[p], nodes=list(g.prim_nodes[p]))
             for p in (0, 1, 2)]
    own = NS(pipes=pipes, prim_states={"f": st})
    page = NS(_symbol_index=NS())
    fronts = frontiers_of(page, {"f": g}, own)
    # the run's real ends are where heating water begins, at A and at D; B and C are only joints
    assert sorted((f.node, f.reason) for f in fronts) == [("A", REAL_SYSTEM_BOUNDARY), ("D", REAL_SYSTEM_BOUNDARY)]
    assert all(f.reason not in (UNSUPPORTED_STRUCTURE, SECTION_JOINT) for f in fronts)
    # the middle section has joints at both ends: accounted for, not silent
    assert [p.section_joints for p in pipes] == [1, 2, 1]
    s = summary(fronts, pipes, 0.02)
    assert s["silent_pipes"] == [] and s["section_joints"] == 4 and s["open_boundaries"] == 0
