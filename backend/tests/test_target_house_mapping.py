import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.astrology_metadata import identify_target_house_from_query

def test_astrological_queries():
    # Career query -> House 10
    assert identify_target_house_from_query("Will I get a promotion in my career?") == 10
    # Marriage query -> House 7
    assert identify_target_house_from_query("Meri shadi kab hogi?") == 7
    # Wealth query -> House 2
    assert identify_target_house_from_query("Will I save money and build wealth?") == 2

def test_out_of_scope_queries():
    # Out of scope query -> None
    assert identify_target_house_from_query("how to bake a chocolate chip cake?") is None
    # General out of scope -> None
    assert identify_target_house_from_query("who is the president?") is None
    # Math query -> None
    assert identify_target_house_from_query("1 + 1") is None

if __name__ == "__main__":
    print("Running target house mapping tests...")
    try:
        test_astrological_queries()
        print("✅ test_astrological_queries PASSED")
        test_out_of_scope_queries()
        print("✅ test_out_of_scope_queries PASSED")
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        print("❌ TEST FAILED")
        sys.exit(1)
