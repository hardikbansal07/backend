# Diagnostic script to check Vimsottari dasha output counts
from jhora.panchanga import drik
from jhora.horoscope.dhasa.graha import vimsottari
from jhora import utils

# Sample birth: 1990-01-01 06:30:00 in Chennai (UTC+5.5)
dob = drik.Date(1990,1,1)
tob = (6,30,0)
place = drik.Place('Chennai,IN', 13.0827, 80.2707, 5.5)

jd = utils.julian_day_number(dob, tob)
print('Julian day:', jd)

# Default call: include_antardhasa=True
balance, periods = vimsottari.get_vimsottari_dhasa_bhukthi(jd, place, include_antardhasa=True)
print('\nDefault call (include_antardhasa=True):')
print('Balance:', balance)
print('Returned periods count:', len(periods))
print('Sample first 12 periods:')
for i, p in enumerate(periods[:12]):
    print(i+1, p)

# Call with include_antardhasa=False (should return 9 mahadashas)
bal2, periods2 = vimsottari.get_vimsottari_dhasa_bhukthi(jd, place, include_antardhasa=False)
print('\ninclude_antardhasa=False:')
print('Balance:', bal2)
print('Periods count (expected 9):', len(periods2))
for i,p in enumerate(periods2):
    print(i+1, p)

# Call with use_rasi_bhukthi_variation True
bal3, periods3 = vimsottari.get_vimsottari_dhasa_bhukthi(jd, place, include_antardhasa=True, use_rasi_bhukthi_variation=True)
print('\nuse_rasi_bhukthi_variation=True:')
print('Periods count:', len(periods3))
print('First 8:', periods3[:8])

# Quick summary expectations
expected_antardasa_count = 9 * 9  # 9 mahadasa * 9 antardasa each
print('\nExpected antardasa count (9*9):', expected_antardasa_count)
print('Match default include_antardhasa count?', len(periods) == expected_antardasa_count)

print('\nDone.')
