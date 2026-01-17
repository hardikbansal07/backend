import sys, os
import pytest
# Ensure the project's src/ is on sys.path so `import jhora` works during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from jhora.ui.formatting import format_vimsottari_chain

@pytest.mark.parametrize("chain,expected",[
    ("Mars♂-Mars♂-Jupiter♃","MD:Ma → AD:Ma → PD:Ju"),
    ("Mercury♀","MD:Me"),
    ("Sun-Moon-Mars-Mercury-Jupiter-Venus","MD:Su → AD:Mo → PD:Ma → SD:Me → PAD:Ju → L6:Ve"),
    ("","")
])
def test_format_vimsottari_chain(chain, expected):
    assert format_vimsottari_chain(chain) == expected
