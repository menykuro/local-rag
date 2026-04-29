"""Pruebas unitarias de persistencia y normalizacion de configuracion runtime."""

import json


def test_watch_config_migrates_legacy_list(temp_runtime_settings):
    import app.core.config as config

    temp_runtime_settings.write_text(
        json.dumps({"watch_folders": ["C:\\legacy\\folder"]}),
        encoding="utf-8",
    )

    folders = config.get_watch_folders()
    assert len(folders) == 1
    assert folders[0]["active"] is True
    assert folders[0]["recursive"] is True
    assert folders[0]["path"].endswith("legacy\\folder")

    saved = json.loads(temp_runtime_settings.read_text(encoding="utf-8"))
    assert isinstance(saved["watch_folders"][0], dict)


def test_watch_config_deduplicates_paths(temp_runtime_settings):
    import app.core.config as config

    config.save_watch_folders(
        [
            {"path": "C:\\data\\same", "active": True, "recursive": True},
            {"path": "C:\\data\\same\\..\\same", "active": False, "recursive": False},
        ]
    )
    folders = config.get_watch_folders()
    assert len(folders) == 1
    assert folders[0]["path"].endswith("data\\same")


def test_upsert_set_active_remove_watch_folder(temp_runtime_settings):
    import app.core.config as config

    created = config.upsert_watch_folder("C:\\my\\folder", active=True, recursive=True)
    assert created["active"] is True

    updated = config.upsert_watch_folder("C:\\my\\folder", active=False, recursive=False)
    assert updated["active"] is False
    assert updated["recursive"] is False

    assert config.set_watch_folder_active("C:\\my\\folder", True) is True
    assert config.set_watch_folder_active("C:\\missing\\folder", False) is False

    assert config.remove_watch_folder("C:\\my\\folder") is True
    assert config.remove_watch_folder("C:\\my\\folder") is False

