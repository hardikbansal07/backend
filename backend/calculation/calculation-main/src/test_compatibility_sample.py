import sys
import os

# Add parent directories to sys.path so we can import jhora
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import Ashtakoota
from jhora.horoscope.match.compatibility import Ashtakoota

def demo_compatibility():
    # Boy: Hasta (13), Pada 1
    # Girl: Anuradha (17), Pada 2
    boy_nak = 13
    boy_pada = 1
    girl_nak = 17
    girl_pada = 2

    print(f"--- MATCHMAKING COMPATIBILITY DEMO ---")
    print(f"Boy Star: Hasta (Index 13), Pada 1")
    print(f"Girl Star: Anuradha (Index 17), Pada 2\n")

    # 1. North Indian Style (Ashtakoota - Max Score 36)
    print("=== NORTH INDIAN STYLE (ASHTAKOOTA - Max 36) ===")
    ak_north = Ashtakoota(boy_nak, boy_pada, girl_nak, girl_pada, method="North")
    res_north = ak_north.compatibility_score()
    
    ettu_list = [
        'Varna Porutham', 'Vasiya Porutham', 'Gana Porutham', 'Dina/Tara Porutham', 
        'Yoni Porutham', 'Adhipathi Porutham', 'Raasi Porutham', 'Naadi Porutham'
    ]
    
    for i, name in enumerate(ettu_list):
        print(f"  - {name}: {res_north[i]} points")
    print(f"  => Total Score: {res_north[8]} out of 36")
    print(f"  - Mahendra Porutham: {res_north[9]}")
    print(f"  - Vedha Porutham: {res_north[10]}")
    print(f"  - Rajju Porutham: {res_north[11]}")
    print(f"  - Sthree Dheerga Porutham: {res_north[12]}\n")

    # 2. South Indian Style (10 Poruthams - Max Score 10)
    print("=== SOUTH INDIAN STYLE (10 PORUTHAMS - Max 10) ===")
    ak_south = Ashtakoota(boy_nak, boy_pada, girl_nak, girl_pada, method="South")
    res_south = ak_south.compatibility_score()
    
    south_list = [
        'Varna Porutham', 'Vasiya Porutham', 'Gana Porutham', 'Dina Porutham', 
        'Yoni Porutham', 'Adhipathi Porutham', 'Raasi Porutham', 'Naadi Porutham'
    ]
    
    for i, name in enumerate(south_list):
        print(f"  - {name}: {res_south[i]} (Match: {bool(res_south[i])})")
    print(f"  => Total Matches: {res_south[8]} out of 10")
    print(f"  - Mahendra Porutham: {res_south[9]} (Match: {bool(res_south[9])})")
    print(f"  - Vedha Porutham: {res_south[10]} (Match: {bool(res_south[10])})")
    print(f"  - Rajju Porutham: {res_south[11]} (Match: {bool(res_south[11])})")
    print(f"  - Sthree Dheerga Porutham: {res_south[12]} (Match: {bool(res_south[12])})")
    if len(res_south) > 13:
        print(f"  - Minimum Porutham: {res_south[13]} (Match: {bool(res_south[13])})")

if __name__ == "__main__":
    demo_compatibility()
