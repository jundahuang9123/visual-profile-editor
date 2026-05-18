import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

UPSTREAM_SRC = ROOT.parent / 'General-Ontology-Editor' / 'src'
if UPSTREAM_SRC.exists():
    sys.path.insert(0, str(UPSTREAM_SRC))
