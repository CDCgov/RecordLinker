from recordlinker.utils import normalize as utils


class TestNormalize:
    def test_normalize(self):
        text = " José O'Hara"
        assert utils.normalize(text) == "joseohara"

        text = "321 Main St."
        assert utils.normalize(text) == "321mainst"

        text = "Crème brûlée 50%"
        assert utils.normalize(text) == "cremebrulee50"
