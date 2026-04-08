"""Tests for application configuration persistence."""

from pathlib import Path

from meshscope.core.config import AppConfig, load_config, save_config


class TestAppConfigDefaults:
    def test_default_version(self) -> None:
        config = AppConfig()
        assert config.version == 1

    def test_default_preset(self) -> None:
        config = AppConfig()
        assert config.get("print_bed", "preset") == "ender_3"

    def test_default_custom_dimensions(self) -> None:
        config = AppConfig()
        assert config.get("print_bed", "custom_x") == 220
        assert config.get("print_bed", "custom_y") == 220
        assert config.get("print_bed", "custom_z") == 250

    def test_set_and_get(self) -> None:
        config = AppConfig()
        config.set("print_bed", "preset", "prusa_mk4")
        assert config.get("print_bed", "preset") == "prusa_mk4"


class TestConfigSaveLoad:
    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        config = AppConfig()
        config.set("print_bed", "preset", "voron_2_4")
        config_path = tmp_path / "config.json"
        save_config(config, config_path)
        loaded = load_config(config_path)
        assert loaded.get("print_bed", "preset") == "voron_2_4"

    def test_load_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "nonexistent.json"
        config = load_config(config_path)
        assert config.get("print_bed", "preset") == "ender_3"

    def test_load_corrupt_file_returns_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text("not json{{{")
        config = load_config(config_path)
        assert config.version == 1
        assert config.get("print_bed", "preset") == "ender_3"

    def test_load_wrong_version_returns_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text('{"version": 999}')
        config = load_config(config_path)
        assert config.version == 1

    def test_load_missing_keys_fills_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text('{"version": 1, "print_bed": {"preset": "bambu_x1c"}}')
        config = load_config(config_path)
        assert config.get("print_bed", "preset") == "bambu_x1c"
        assert config.get("print_bed", "custom_x") == 220

    def test_save_atomic_creates_file(self, tmp_path: Path) -> None:
        config = AppConfig()
        config_path = tmp_path / "config.json"
        save_config(config, config_path)
        assert config_path.exists()
        assert config_path.stat().st_size > 0

    def test_save_no_temp_files_left(self, tmp_path: Path) -> None:
        config = AppConfig()
        config_path = tmp_path / "config.json"
        save_config(config, config_path)
        files = list(tmp_path.iterdir())
        assert len(files) == 1
