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

    def test_api_root_path(self):
        obj = config.Settings()
        assert obj.api_root_path == "/api"

        with pytest.raises(ValueError):
            config.Settings(api_root_path="")

        with pytest.raises(ValueError):
            config.Settings(api_root_path="/")

        obj = config.Settings(api_root_path="myapi")
        assert obj.api_root_path == "/myapi"

        obj = config.Settings(api_root_path="myapi/")
        assert obj.api_root_path == "/myapi"
