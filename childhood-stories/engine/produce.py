#!/usr/bin/env python3
"""Render and QC one Childhood Stories episode.

usage: python3 engine/produce.py episodes/<folder>/episode.py [--cover-only] [--no-qc] [--keep]
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cs import film, qc

ap = argparse.ArgumentParser()
ap.add_argument("episode")
ap.add_argument("--cover-only", action="store_true")
ap.add_argument("--preview", action="store_true", help="quick stills + timing only")
ap.add_argument("--no-qc", action="store_true")
ap.add_argument("--resume", action="store_true", help="reuse shot segments already rendered in _work/ (retry a failed later stage)")
ap.add_argument("--keep", action="store_true", help="keep per-shot video segments in _work/")
a = ap.parse_args()
d = os.path.dirname(os.path.abspath(a.episode))
if a.preview:
    film.preview(a.episode, d)
    sys.exit(0)
film.produce(a.episode, d, only_cover=a.cover_only, keep_segments=a.keep, resume=a.resume)
if not a.cover_only and not a.no_qc:
    rep = qc.run_qc(d)
    print(json.dumps({k: rep[k] for k in ("pass", "blocking", "warnings", "checks")}, indent=1))
    sys.exit(0 if rep["pass"] else 2)
