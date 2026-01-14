from src.api import service, models
from datetime import datetime, timezone

# Build request
loc = models.LocationIn(place='Test', latitude=28.6139, longitude=77.2090, tzOffset=5.5)
req = models.HoroscopeRequest(
    birthDateTime = datetime(1990,1,1,12,0,0,tzinfo=timezone.utc),
    location = loc,
    divisionalFactors=[36,72]
)
sh = service.compute_horoscope(req)
# get internal horoscope instance
horo = sh.internalHoroscope
for factor in (36,72):
    print('\n=== chart_info for D{}'.format(factor))
    chart_info, chart_houses, asc = horo.get_horoscope_information_for_chart(divisional_chart_factor=factor)
    for k,v in chart_info.items():
        print('KEY:', k)
        print('  ->', v)
print('\nINSPECT_DONE')
