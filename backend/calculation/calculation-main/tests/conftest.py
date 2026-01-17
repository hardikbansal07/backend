import pathlib
import sys

# Ensure repository root is importable for `src` package imports during tests
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def pytest_ignore_collect(path, config):  # type: ignore
    # Skip heavy UI/Qt test in headless automated runs
    if pathlib.Path(str(path)).name == 'test_ui.py':
        return True
    return False