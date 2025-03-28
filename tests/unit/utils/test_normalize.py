from recordlinker.utils import normalize as utils


class TestNormalizeText:
    def test_normalize_text(self):
        text = " José O'Hara"
        assert utils.normalize_text(text) == "joseohara"

        text = "321 Main St."
        assert utils.normalize_text(text) == "321mainst"

        text = "Crème brûlée 50%"
        assert utils.normalize_text(text) == "cremebrulee50"


class TestNormalizePhoneNumber:
    def test_normalize_phone_number(self):
        phone = "223-456-7890"
        assert utils.normalize_phone_number(phone) == "2234567890"

        phone = "223 456 7890"
        assert utils.normalize_phone_number(phone) == "2234567890"

        phone = "223-456-7890 ex 456"
        assert utils.normalize_phone_number(phone) == "2234567890"

        phone = "+1 223-456-7890"
        assert utils.normalize_phone_number(phone) == "2234567890"

        phone = "+1 223-456-7890 ext 456"
        assert utils.normalize_phone_number(phone) == "2234567890"

        phone = "+44 223-456-7890 x 456"
        assert utils.normalize_phone_number(phone) == "2234567890"

        # Test example showing the limit of the normalization
        phone = "44 223-456-7890 456"
        assert utils.normalize_phone_number(phone) == "442234567890456"
