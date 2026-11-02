"""A label naming two pipes laid side by side names that pair, whichever code it writes first.

`VV01-53-/KV01-53-20` and, further along the same pair, `KV01-53-/VV01-53-20`: the hot and the cold water run
together and the drawing labels them once for both, the size once at the end. Held in the order written the two
labels were two identities claiming one run, the run was left to neither, and nine metres had no name.

The same list also makes the second code a system. It never stands first in such a label, so judged by the
label's head alone the cold water of a whole sheet was a material - while the list's own words say KALLVATTEN-
LEDNING. Those words count too, through what the lettering failed to read: SPI??VATTEN?EDNING is spill water.

And the system number a placeholder stands for (KVXX-53) is written in digits: KVO1 read from the strokes is KV01.
"""
from types import SimpleNamespace

from vvs_engine.pipes.ownership import identity_from_text
from vvs_engine.semantics.legend import DrawingLegend, LegendEntry, assign_roles, number_as_listed, role_from_words


def test_a_pair_is_the_same_identity_in_either_order():
    a = identity_from_text("VV01-53-/KV01-53-20", 20, "VV01", None)
    b = identity_from_text("KV01-53-/VV01-53-20", 20, "KV01", None)
    assert a.base == b.base and a.dn == b.dn == 20
    assert identity_from_text("VV01-53-/KV01-53-16", 16, "VV01", None).base == a.base     # the size stays apart


def test_a_single_label_and_a_size_qualifier_are_read_as_before():
    assert identity_from_text("KV2-K1-35", 35, "KV2", None).base == "KV2-K1"
    assert identity_from_text("VV1-K1-22/W", 22, "VV1", None).base == "VV1-K1-W"
    assert identity_from_text("S3-R8-110", 110, "S3", None).base == "S3-R8"
    # a qualifier after a slash is no second pipe: both ways of writing the insulation class are one pipe
    assert identity_from_text("KV1-K1/S2-22", 22, "KV1", None).base == identity_from_text(
        "KV1-K1-22/S2", 22, "KV1", None).base


def _entry(code, description, y):
    return LegendEntry(code=code, description=description, heading="", bbox=(1000.0, y, 1100.0, y + 4.0))


def _label(text, dn, x):
    toks = text.replace("/", "-").split("-")
    return SimpleNamespace(did=f"{text}@{x}", text=text, system_token=toks[0], tokens=[t for t in toks if t], dn=dn,
                           dn_source="inline", pattern="A9-9-/A9-9-9", bbox=(x, 300.0, x + 40.0, 305.0))


def test_the_second_code_of_a_pair_label_is_a_system():
    legend = DrawingLegend(entries=[_entry("VVXX-3", "VARMVATTEN", 100), _entry("KVXX-3", "KOPPAR", 110),
                                    _entry("KBXX-3", "KOPPAR", 120)])
    assign_roles(legend, [_label("VV02-3-/KV02-3-15", 15, 100), _label("VV02-3-/KV02-3-16", 16, 200),
                          _label("KB02-3-35", 35, 300)])
    assert {e.code: e.role for e in legend.entries}["KVXX-3"] == "system"


def test_a_listed_medium_counts_through_unread_letters_and_a_ledning():
    assert role_from_words("SPI??VATTEN?EDNING/ KOPPAR") == "system"
    assert role_from_words("KALLVATTENLEDNING, PEM-RÖR") == "system"
    assert role_from_words("?????LEDNING") is None                   # nothing left that agrees
    assert role_from_words("RENSRÖR MED LOCK") is None
    assert role_from_words("BACKVENTIL") == "component"


def test_the_system_number_a_placeholder_stands_for_is_written_in_digits():
    codes = ["KVXX-53", "VVXX-53", "VVXX-3", "KVXX-3", "VSXX-22"]
    assert number_as_listed("KVO1-53-/VVO1-53-16", codes) == "KV01-53-/VV01-53-16"
    assert number_as_listed("VVOZ-3-/KVOZ-3-15", codes) == "VV02-3-/KV02-3-15"
    assert number_as_listed("VSO2-22-12", codes) == "VS02-22-12"
    assert number_as_listed("KV2-K1-35", codes) == "KV2-K1-35"             # no placeholder code: as read
    assert number_as_listed("KVO1-53-16", []) == "KVO1-53-16"
