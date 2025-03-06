import pytest

import recordlinker.utils.normalize as normalize


class TestPIINormalizeState:
    def test_normalize_state(self):
        assert normalize.normalize_state("california") == "CA"
        assert normalize.normalize_state("California") == "CA"
        assert normalize.normalize_state("CALIFORNIA") == "CA"
        assert normalize.normalize_state("CA") == "CA"
        assert normalize.normalize_state("ca") == "CA"
        assert normalize.normalize_state(None) is None
        with pytest.raises(ValueError):
            normalize.normalize_state("unknown")
