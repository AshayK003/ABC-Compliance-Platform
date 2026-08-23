"""One-off: shrink frontend/src/assets/india-states.geojson for bundle size.

Strategy (no external deps):
  1. Round all coordinates to 3 decimal places (~110m precision — far beyond
     what a country-level choropleth needs).
  2. Drop polygon rings below a vertex threshold (tiny coastal islands that
     are invisible at dashboard zoom).
Prints before/after sizes so the win is verifiable.
"""
import json
import os
import sys

PATH = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "assets", "india-states.geojson")
MIN_RING_VERTICES = int(sys.argv[1]) if len(sys.argv) > 1 else 12
COORD_DIGITS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
MIN_STEP_DEG = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01


def round_ring(ring):
    return [[round(x, COORD_DIGITS), round(y, COORD_DIGITS)] for x, y in ring]


def _dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def decimate_ring(ring):
    """Drop vertices closer than MIN_STEP_DEG degrees to the last kept vertex.

    Country-level choropleths are drawn a few hundred px wide; sub-kilometre
    coastal detail is invisible. Closed rings always keep first==last.
    """
    if len(ring) <= 4:
        return ring
    min_step2 = MIN_STEP_DEG * MIN_STEP_DEG
    out = [ring[0]]
    for pt in ring[1:-1]:
        if _dist2(pt, out[-1]) >= min_step2:
            out.append(pt)
    out.append(ring[-1])
    # collapse consecutive duplicates created by rounding
    deduped = [out[0]]
    for pt in out[1:]:
        if pt != deduped[-1]:
            deduped.append(pt)
    if len(deduped) > 1 and deduped[0] == deduped[-1] and len(deduped) <= 4:
        return None
    return deduped if len(deduped) >= 4 else None


def shrink_geometry(geom):
    t = geom.get("type")
    if t == "Polygon":
        rings = []
        for r in geom["coordinates"]:
            d = decimate_ring(r)
            if d and len(d) >= MIN_RING_VERTICES:
                rings.append(round_ring(d))
        if not rings:
            return None
        geom["coordinates"] = rings
        return geom
    if t == "MultiPolygon":
        polys = []
        for poly in geom["coordinates"]:
            kept = []
            for r in poly:
                d = decimate_ring(r)
                if d and len(d) >= MIN_RING_VERTICES:
                    kept.append(round_ring(d))
            if kept:
                polys.append(kept)
        if not polys:
            return None
        geom["coordinates"] = polys
        return geom
    return geom


def main():
    before = os.path.getsize(PATH)
    with open(PATH, encoding="utf-8") as f:
        data = json.load(f)

    kept_features = []
    dropped = 0
    for feature in data.get("features", []):
        geom = feature.get("geometry")
        if not geom:
            continue
        shrunk = shrink_geometry(geom)
        if shrunk is None:
            dropped += 1
            continue
        feature["geometry"] = shrunk
        kept_features.append(feature)
    data["features"] = kept_features

    out = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(out)

    after = os.path.getsize(PATH)
    print(f"before: {before/1e6:.1f} MB")
    print(f"after:  {after/1e6:.2f} MB  ({before/max(after,1):.0f}x smaller)")
    print(f"features kept: {len(kept_features)}, dropped (all-specks): {dropped}")
    if after > 2_000_000:
        print("WARNING: still above 2MB — consider MIN_RING_VERTICES bump", file=sys.stderr)


if __name__ == "__main__":
    main()
