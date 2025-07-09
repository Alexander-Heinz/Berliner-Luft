# conftest.py
import sys
from pathlib import Path

# 1) Compute absolute path to the `src/` folder
SRC = Path(__file__).parent / "src"

# 2) Insert it *before* everything else on sys.path
sys.path.insert(0, str(SRC))
