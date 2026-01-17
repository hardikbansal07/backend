import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from jhora import utils


def test_get_elevation_returns_float(monkeypatch):
    """Ensure get_elevation returns a float without raising exceptions."""

    class DummyResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"results": [{"elevation": 123.45}]}

    monkeypatch.setattr(utils.requests, "get", lambda *args, **kwargs: DummyResponse())

    result = utils.get_elevation(10.0, 20.0)

    assert isinstance(result, float)
    assert result == pytest.approx(123.45)

