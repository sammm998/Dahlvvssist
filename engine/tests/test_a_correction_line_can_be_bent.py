"""Ett rättelsestreck går att böja: flytta en punkt, lägga in en ny på ett segment, ta bort en.

Den som rättar ett rör ska kunna få linjen att följa röret runt hörnen i efterhand, inte bara rita om den.
Punktfunktionerna är skrivna i TypeScript och delas med vyn, så provet körs där koden lever: den buntas med
esbuild och körs i node (frontend/src/edit/bend.test.ts). Provet här är bara sändebudet.
"""
import os
import subprocess

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONT = os.path.join(ROOT, "frontend")
ESBUILD = os.path.join(FRONT, "node_modules", ".bin", "esbuild")


@pytest.mark.skipif(not os.path.exists(ESBUILD), reason="frontend/node_modules saknas")
def test_a_correction_line_can_be_bent(tmp_path):
    out = str(tmp_path / "bend.test.js")
    b = subprocess.run([ESBUILD, "src/edit/bend.test.ts", "--bundle", "--platform=node", "--format=cjs", f"--outfile={out}",
                        "--log-level=warning"], cwd=FRONT, capture_output=True, text=True, timeout=120)
    assert b.returncode == 0, b.stderr
    r = subprocess.run(["node", out], capture_output=True, text=True, timeout=120)
    failed = [ln for ln in r.stdout.splitlines() if ln.startswith("  FEL")]
    assert r.returncode == 0 and not failed, "\n".join(failed) + "\n" + r.stderr[-800:]
    assert "alla böjningar håller" in r.stdout
