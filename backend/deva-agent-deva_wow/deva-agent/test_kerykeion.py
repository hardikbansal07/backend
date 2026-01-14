from kerykeion import KrInstance, Report
from datetime import datetime

# Current time
now = datetime.now()

# Create a chart for "Now" (Transit)
# Location defaults to London if not specified, but for Transits, planet positions relative to Earth are roughly same everywhere (geocentric) 
# except for Moon. We'll stick to a generic location or the user's location if known. 
# Using New Delhi as standard reference for Vedic testing.
t = KrInstance("Transit", now.year, now.month, now.day, now.hour, now.minute, "New Delhi", "IN")

# Kerykeion default is Tropical. We need Sidereal.
# Kerykeion supports 'sidereal_mode' in some versions or we might need to subtract Ayanamsa.
# Let's check available attributes to find Lahiri or Sidereal options.
print("--- Kerykeion Objects ---")
# print(dir(t))

# By default Kerykeion might be Tropical. Let's see if we can get Sidereal.
# If not, we might need pyswisseph directly, but kerykeion wraps it.
# Let's check the report.
report = Report(t)
print(f"Sun (Tropical): {report.sun['position']}")
print(f"Saturn (Tropical): {report.saturn['position']}")

# IMPORTANT: Vedic uses Sidereal. Tropical Saturn is ~23-24 deg diff.
# If Tropical Saturn is in Aries, Sidereal is in Pisces.
# Currently (Dec 2025):
# Web says Saturn Sidereal = Pisces 1-5 deg.
# Tropical Saturn would be ~ Pisces + 24 deg = Aries ~0 deg.
# Let's check what we get.

print("\n--- Raw Data ---")
print(f"Saturn Abs Degree: {t.saturn['abs_pos']}")
