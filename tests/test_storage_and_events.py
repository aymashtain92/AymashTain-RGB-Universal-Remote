from __future__ import annotations

from aymashtain.config import Settings
from aymashtain.events import EventBus, SessionLogger
from aymashtain.storage import Database


def test_database_seeds_default_profile(tmp_path):
    db = Database(tmp_path / "test.db")
    profiles = db.get_profiles()
    assert profiles
    buttons = db.get_buttons(profiles[0].id)
    assert any(button.hex == "BC01010155" for button in buttons)
    assert any(button.is_macro for button in buttons)
    db.close()


def test_button_crud(tmp_path):
    db = Database(tmp_path / "test.db")
    profile_id = db.create_profile("Test profile")
    button_id = db.add_button(profile_id, "Red", "BC0406000003E8000055", group_name="Colours")
    assert db.get_button(button_id).label == "Red"
    db.update_button(button_id, label="Crimson")
    assert db.get_button(button_id).label == "Crimson"
    clone_id = db.clone_button(button_id)
    assert clone_id is not None and clone_id != button_id
    db.delete_button(button_id)
    assert db.get_button(button_id) is None
    db.close()


def test_command_history(tmp_path):
    db = Database(tmp_path / "test.db")
    db.add_command("BC01010155", label="test", ok=True)
    rows = db.get_commands()
    assert rows[0]["hex"] == "BC01010155"
    db.clear_commands()
    assert db.get_commands() == []
    db.close()


def test_devices(tmp_path):
    db = Database(tmp_path / "test.db")
    db.upsert_device("41:42:59:F1:C8:68", "Strip 1")
    db.upsert_device("41:42:59:F1:C8:68", "Strip 1 renamed")
    assert len(db.get_devices()) == 1
    db.forget_device("41:42:59:F1:C8:68")
    assert db.get_devices() == []
    db.close()


def test_event_bus_drain_and_history():
    bus = EventBus()
    bus.emit("info", "hello")
    bus.emit("error", "bad")
    drained = bus.drain()
    assert [event.kind for event in drained] == ["info", "error"]
    assert bus.drain() == []
    assert len(bus.history()) == 2


def test_session_logger_writes_files(tmp_path):
    logger = SessionLogger(directory=tmp_path, retention_days=3)
    bus = EventBus(session_logger=logger)
    bus.emit("send", "BC01010155")
    logger.flush_json()
    assert list(tmp_path.glob("session_*.log"))
    assert list(tmp_path.glob("session_*.json"))
    assert list(tmp_path.glob("session_*.csv"))


def test_settings_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    settings = Settings.load(path)
    settings.last_brightness = 42
    settings.known_devices = [{"address": "AA:BB", "name": "Strip"}]
    settings.save()
    assert Settings.load(path).last_brightness == 42
