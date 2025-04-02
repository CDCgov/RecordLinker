import pytest
from recordlinker import config


class TestSettings:
    def test_configure_logging_invalid_file(self):
        obj = config.Settings(log_config="invalid.json")
        with pytest.raises(config.ConfigurationError):
            obj.configure_logging()

    def test_configure_logging(self):
        obj = config.Settings(log_config="assets/production_log_config.json")
        assert obj.configure_logging() is None
