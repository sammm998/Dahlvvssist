/* Att böja ett streck: flytta en punkt, lägga in en ny på ett segment, ta bort en.
 *
 * En rättelse eller markering är en lista punkter i bladets egna koordinater. Den som rättar ett rör ska kunna få
 * linjen att följa röret runt hörnen i efterhand, inte bara rita om den från början. Funktionerna här rör bara
 * punktlistan; vyn och sparandet bygger på dem.
 */
export type P = number[];

export const dist = (a: P, b: P) => Math.hypot(b[0] - a[0], b[1] - a[1]);
export const pathLen = (pts: P[]) => pts.slice(1).reduce((s, q, i) => s + dist(pts[i], q), 0);

/** Punkten i flyttad till p. */
export function movePoint(pts: P[], i: number, p: P): P[] {
  if (i < 0 || i >= pts.length) return pts;
  return pts.map((q, k) => (k === i ? [p[0], p[1]] : q));
}

/** En ny brytpunkt p efter punkt seg, alltså på segmentet seg -> seg+1. Returnerar listan och den nya punktens index. */
export function insertPoint(pts: P[], seg: number, p: P): { points: P[]; index: number } {
  if (seg < 0 || seg >= pts.length - 1) return { points: pts, index: -1 };
  return { points: [...pts.slice(0, seg + 1), [p[0], p[1]], ...pts.slice(seg + 1)], index: seg + 1 };
}

/** Punkten i borttagen - men ett streck har alltid minst två punkter kvar. */
export function removePoint(pts: P[], i: number): P[] {
  if (pts.length <= 2 || i < 0 || i >= pts.length) return pts;
  return pts.filter((_, k) => k !== i);
}

/** Mittpunkten på varje segment: där man tar tag för att böja. */
export function midpoints(pts: P[]): P[] {
  return pts.slice(1).map((q, i) => [(pts[i][0] + q[0]) / 2, (pts[i][1] + q[1]) / 2]);
}

/** Närmaste punkt inom tol, eller -1. */
export function nearestGrip(pts: P[], p: P, tol: number): number {
  let best = -1, bd = tol;
  pts.forEach((q, i) => { const d = dist(q, p); if (d <= bd) { bd = d; best = i; } });
  return best;
}

/** Närmaste segmentmitt inom tol, eller -1 (segmentets index). */
export function nearestMid(pts: P[], p: P, tol: number): number {
  return nearestGrip(midpoints(pts), p, tol);
}
