/* Att böja ett streck, provat mot tal räknade för hand. Körs med node efter esbuild
 * (se engine/tests/test_a_correction_line_can_be_bent.py). */
import { insertPoint, midpoints, movePoint, nearestGrip, nearestMid, pathLen, removePoint } from "./bend";

declare const process: any;
let failures = 0;
const check = (name: string, ok: boolean, detail?: unknown) => {
  if (ok) console.log(`  ok  ${name}`); else { failures++; console.log(`  FEL ${name}${detail !== undefined ? ": " + JSON.stringify(detail) : ""}`); }
};
const near = (a: number, b: number) => Math.abs(a - b) <= 1e-6;

const line = [[0, 0], [100, 0]];
const ins = insertPoint(line, 0, [50, 0]);
check("en ny brytpunkt läggs in mitt på", ins.index === 1 && near(pathLen(ins.points), 100), ins);
const bent = movePoint(ins.points, ins.index, [50, 50]);
check("dras brytpunkten ut blir linjen längre", near(pathLen(bent), 2 * Math.hypot(50, 50)), pathLen(bent));
check("originalet är orört", JSON.stringify(line) === "[[0,0],[100,0]]");
const three = [[0, 0], [50, 50], [100, 0]];
check("en punkt tas bort", JSON.stringify(removePoint(three, 1)) === "[[0,0],[100,0]]");
check("ett streck har alltid två punkter kvar", removePoint(line, 0) === line);
check("greppet hittas inom toleransen", nearestGrip(three, [52, 49], 5) === 1);
check("inget grepp utanför toleransen", nearestGrip(three, [70, 70], 5) === -1);
check("segmentens mitt", JSON.stringify(midpoints(three)) === "[[25,25],[75,25]]");
check("segmentets mitt hittas", nearestMid(three, [74, 26], 5) === 1);
check("felaktigt index lämnar linjen", movePoint(line, 5, [1, 1]) === line && insertPoint(line, 3, [1, 1]).index === -1);

if (failures) { console.log(`${failures} påståenden föll`); process.exit(1); }
console.log("alla böjningar håller");
