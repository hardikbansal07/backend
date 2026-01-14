import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
# ensure project root and src are on sys.path so imports work under pytest
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

from src.api import service, models
from datetime import datetime, timezone


def test_divisional_planet_longitudes():
    loc = models.LocationIn(place='Test', latitude=28.6139, longitude=77.2090, tzOffset=5.5)
    req = models.HoroscopeRequest(birthDateTime=datetime(1990,1,1,12,0,0,tzinfo=timezone.utc), location=loc)
    sh = service.compute_horoscope(req)
    resp = sh.response
    assert resp.divisionalCharts, "No divisional charts returned"
    for dc in resp.divisionalCharts:
        # At least one planet expected
        assert dc.planets and len(dc.planets) > 0, f"No planets in D{dc.factor}"
        for p in dc.planets:
            # rawLongitudeDeg should be present and numeric
            assert getattr(p, 'rawLongitudeDeg', None) is not None, f"Missing rawLongitudeDeg for {p.name} in D{dc.factor}"
            # longitudeDMS should be a non-empty string
            dms = getattr(p, 'longitudeDMS', None)
            assert dms is not None and str(dms).strip() != '', f"Missing longitudeDMS for {p.name} in D{dc.factor}"
            # retrograde should be a bool
            retro = getattr(p, 'retrograde', None)
            assert isinstance(retro, bool), f"retrograde flag not boolean for {p.name} in D{dc.factor}"
            # nakshatra/pada if present must be valid
            nk = getattr(p, 'nakshatra', None)
            npada = getattr(p, 'nakshatraPada', None)
            if nk is not None:
                assert isinstance(nk, str) and nk.strip() != '', f"nakshatra present but empty for {p.name} in D{dc.factor}"
            if npada is not None:
                assert isinstance(npada, int) and 1 <= npada <= 4, f"nakshatraPada invalid for {p.name} in D{dc.factor}: {npada}"
            # isCombust and isVargottama should be bool or None
            ic = getattr(p, 'isCombust', None)
            iv = getattr(p, 'isVargottama', None)
            assert ic in (True, False, None), f"isCombust invalid type for {p.name} in D{dc.factor}"
            assert iv in (True, False, None), f"isVargottama invalid type for {p.name} in D{dc.factor}"
