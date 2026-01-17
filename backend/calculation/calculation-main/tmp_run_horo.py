from src.api import service, models
from datetime import datetime, timezone

# Build a minimal valid HoroscopeRequest using input models from API
loc = models.LocationIn(place='Test', latitude=28.6139, longitude=77.2090, tzOffset=5.5)
req = models.HoroscopeRequest(
    birthDateTime = datetime(1990,1,1,12,0,0,tzinfo=timezone.utc),
    location = loc,
    divisionalFactors=[36,72]
)
try:
    sh = service.compute_horoscope(req)
    # Inspect object to find divisional charts
    print('Computed StoredHoroscope type:', type(sh))
    # print available attributes
    print('attrs:', [a for a in dir(sh) if not a.startswith('_')])
    # try to find attribute holding horoscope payload
    possible = None
    for name in ['horoscope','data','payload','result']:
        if hasattr(sh, name):
            possible = getattr(sh, name)
            print('Using',name)
            break
    if possible is None:
        # fallback: print the object repr and stop
        print('StoredHoroscope repr:', sh)
    else:
        if hasattr(possible, 'divisionalCharts'):
            charts = possible.divisionalCharts
        else:
            # maybe it's a dict-like
            charts = getattr(possible, 'divisionalCharts', None) or (possible.get('divisionalCharts') if isinstance(possible, dict) else None)
        print('divisionalCharts present? ', charts is not None)
        if charts:
            for d in charts:
                if d.factor in (36,72):
                    print('D',d.factor,'planets:', [p.name for p in d.planets])
except Exception as e:
    import traceback
    traceback.print_exc()
