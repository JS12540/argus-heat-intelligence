import sys
from pathlib import Path

# Make argus_agent importable the same way it is when run locally
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from argus_agent.main import app  # noqa: E402

# Vercel's Python runtime imports this module and looks for `app`
