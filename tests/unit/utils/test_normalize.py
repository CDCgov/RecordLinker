from recordlinker.utils import normalize as utils


class TestNormalize:
    def test_normalize(self):
        text = " José O'Hara"
        assert utils.normalize_text(text) == "joseohara"

        text = "321 Main St."
        assert utils.normalize_text(text) == "321mainst"

        text = "Crème brûlée 50%"
        assert utils.normalize_text(text) == "cremebrulee50"
