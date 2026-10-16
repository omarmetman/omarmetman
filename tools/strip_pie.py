#!/usr/bin/env python3
"""Derive donut-free 3D city SVGs from the action's full output.

The generator has no "city without pie" mode, so we post-process:
  profile-night-rainbow.svg -> profile-3d-contrib/city-night.svg
  profile-green-animate.svg -> profile-3d-contrib/city-day.svg

Only the top-level <g> holding the language donut is removed
(identified by its language labels). City, radar and footer stay intact.
If the layout ever changes, files are copied unchanged (never deleted).
"""
import os
import shutil
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "tools" else HERE
CONTRIB = os.path.join(ROOT, "profile-3d-contrib")

NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", "http://www.w3.org/2000/svg")

PAIRS = [
    ("profile-night-rainbow.svg", "city-night.svg"),
    ("profile-green-animate.svg", "city-day.svg"),
]

LANG_MARKERS = {"JavaScript", "TypeScript", "HTML", "Python"}


def is_pie_group(g):
    texts = {t.text for t in g.iter(NS + "text")}
    return len(texts & LANG_MARKERS) >= 2


def strip(src, dst):
    src_p, dst_p = os.path.join(CONTRIB, src), os.path.join(CONTRIB, dst)
    if not os.path.exists(src_p):
        print(f"skip {dst}: {src} not found")
        return
    try:
        tree = ET.parse(src_p)
    except ET.ParseError as e:
        print(f"skip {dst}: parse error {e}")
        return
    root = tree.getroot()
    removed = False
    for g in [c for c in root if c.tag == NS + "g" and is_pie_group(c)]:
        root.remove(g)
        removed = True
    if removed:
        tree.write(dst_p, encoding="unicode", xml_declaration=False)
        print(f"wrote {dst} (donut removed)")
    else:
        shutil.copyfile(src_p, dst_p)
        print(f"wrote {dst} (no donut found, copied as-is)")


if __name__ == "__main__":
    os.makedirs(CONTRIB, exist_ok=True)
    for src, dst in PAIRS:
        strip(src, dst)
