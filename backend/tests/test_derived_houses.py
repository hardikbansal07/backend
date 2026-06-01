# backend/tests/test_derived_houses.py
import sys
from pathlib import Path

# Add backend directory to Python path
backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import unittest
from services.astrology_metadata import (
    resolve_lagna_sign_id,
    get_house_lord_circuit,
    AstrologicalMatrixEngine
)

class TestDerivedHousesAndMatrixEngine(unittest.TestCase):
    
    def test_resolve_lagna_sign_id(self):
        """Asserts that text sign names are resolved correctly to 1-indexed Vedic IDs."""
        self.assertEqual(resolve_lagna_sign_id("Aries"), 1)
        self.assertEqual(resolve_lagna_sign_id(" Leo "), 5)
        self.assertEqual(resolve_lagna_sign_id("scorpio"), 8)
        self.assertEqual(resolve_lagna_sign_id("Pisces"), 12)
        # Default fallback
        self.assertEqual(resolve_lagna_sign_id("InvalidSignName"), 1)
        self.assertEqual(resolve_lagna_sign_id(None), 1)

    def test_get_physical_house_math(self):
        """Asserts that relative-to-physical house stepping is mathematically correct (anticlockwise inclusive)."""
        # Sibling's Wealth (2nd from 3rd house) = D1 House 4
        self.assertEqual(AstrologicalMatrixEngine.get_physical_house(3, 2), 4)
        
        # Sibling's Career (10th from 3rd house) = D1 House 12
        self.assertEqual(AstrologicalMatrixEngine.get_physical_house(3, 10), 12)
        
        # Career Resignation / Loss (12th from 10th house) = D1 House 9
        self.assertEqual(AstrologicalMatrixEngine.get_physical_house(10, 12), 9)
        
        # Spouse's Wealth (2nd from 7th house) = D1 House 8
        self.assertEqual(AstrologicalMatrixEngine.get_physical_house(7, 2), 8)
        
        # Self's core self (1st from 1st house) = D1 House 1
        self.assertEqual(AstrologicalMatrixEngine.get_physical_house(1, 1), 1)

    def test_resolve_shifted_matrix(self):
        """Asserts that the complete relative-to-physical house matrix maps semantical and sign properties perfectly."""
        # Lagna is Leo (5)
        lagna_sign_id = 5
        # Focus is Career (10)
        main_house = 10
        
        matrix = AstrologicalMatrixEngine.resolve_shifted_matrix(main_house, lagna_sign_id)
        
        # Ensure all 12 houses are present
        self.assertEqual(len(matrix), 12)
        
        # Check Relative House 1 (Lagna of Career = D1 House 10)
        cell_1 = matrix[1]
        self.assertEqual(cell_1["physical_house_number"], 10)
        # Sign in House 10 for Lagna Leo (5) is Taurus (2)
        self.assertEqual(cell_1["zodiac_sign_id"], 2)
        self.assertEqual(cell_1["zodiac_sign_name"], "Taurus")
        self.assertEqual(cell_1["concept"], "House of Self & Beginnings")
        
        # Check Relative House 2 (Wealth of Career = D1 House 11)
        cell_2 = matrix[2]
        self.assertEqual(cell_2["physical_house_number"], 11)
        # Sign in House 11 for Lagna Leo (5) is Gemini (3)
        self.assertEqual(cell_2["zodiac_sign_id"], 3)
        self.assertEqual(cell_2["zodiac_sign_name"], "Gemini")
        self.assertEqual(cell_2["concept"], "House of Wealth, Speech & Assets")
        self.assertEqual(cell_2["classifications"], ["Panaphara"])

    def test_get_house_lord_circuit(self):
        """Asserts that the House Lord Circuit traverses lords correctly and terminates loops cleanly."""
        # Setup mock lord placements
        # Lagna Leo (5)
        # 10th House is Taurus (2), Lord is Venus.
        # Venus placed in 2nd House.
        # 2nd House is Virgo (6), Lord is Mercury.
        # Mercury placed in 11th House.
        # 11th House is Gemini (3), Lord is Mercury (placed in 11th House - Loop!).
        lord_placements = {
            "Venus": 2,
            "Mercury": 11,
            "Sun": 10
        }
        
        lagna_sign_id = 5  # Leo
        start_house = 10
        
        circuit = get_house_lord_circuit(start_house, lagna_sign_id, lord_placements)
        
        # Should follow:
        # Step 1: House 10 (Sign: Taurus, Lord: Venus) -> placed in 2 (5 steps inclusive)
        # Step 2: House 2 (Sign: Virgo, Lord: Mercury) -> placed in 11 (10 steps inclusive)
        # Step 3: House 11 (Sign: Gemini, Lord: Mercury) -> placed in 11 (1 step inclusive - Loop!)
        # Stop. Total length = 3
        
        self.assertEqual(len(circuit), 3)
        
        # Step 1 Assertions:
        self.assertEqual(circuit[0]["house"], 10)
        self.assertEqual(circuit[0]["sign_name"], "Taurus")
        self.assertEqual(circuit[0]["lord"], "Venus")
        self.assertEqual(circuit[0]["placed_house"], 2)
        self.assertEqual(circuit[0]["steps_inclusive"], 5)
        self.assertEqual(circuit[0]["is_bhavat_bhavam"], False)
        
        # Step 2 Assertions:
        self.assertEqual(circuit[1]["house"], 2)
        self.assertEqual(circuit[1]["sign_name"], "Virgo")
        self.assertEqual(circuit[1]["lord"], "Mercury")
        self.assertEqual(circuit[1]["placed_house"], 11)
        self.assertEqual(circuit[1]["steps_inclusive"], 10)
        
        # Step 3 Assertions:
        self.assertEqual(circuit[2]["house"], 11)
        self.assertEqual(circuit[2]["sign_name"], "Gemini")
        self.assertEqual(circuit[2]["lord"], "Mercury")
        self.assertEqual(circuit[2]["placed_house"], 11)
        self.assertEqual(circuit[2]["steps_inclusive"], 1)

if __name__ == "__main__":
    unittest.main()
