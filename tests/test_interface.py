# tests/test_interface.py

import os
import sys
import time
import json
import tempfile
import unittest
from pathlib import Path

# ------------------------------------------------------------
# Asegurar que la raiz este en el path
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import Config
from app.core.state import State, GestureType

from app.interface.controls import ControlsController, ControlAction
from app.interface.settings import (
    SettingsController,
    SettingsProfile,
    DEFAULT_SETTINGS,
)
from app.interface.preview import PreviewController, PreviewMode, OverlayType


# ============================================================
# CONTROLS
# ============================================================

class DummyEngine:
    """Motor dummy para probar el ControlsController."""

    def __init__(self):
        self.state = State()
        self.started = False
        self.stopped = False
        self.spoken = []
        self.gestures = []
        self.recording_path = None
        self.recording_stopped = False
        self.avatar_loader = None
        self.motion_engine = None

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def speak(self, text, **kwargs):
        self.spoken.append(text)

    def set_gesture(self, gesture):
        self.gestures.append(gesture)

    def start_recording(self, path):
        self.recording_path = path

    def stop_recording(self):
        self.recording_stopped = True
        return 1.5

    def export_video(self, path):
        return True


class TestControlsController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.ensure_directories()
        self.engine = DummyEngine()
        self.controls = ControlsController(self.config, engine=self.engine)

    def test_initial(self):
        self.assertIs(self.controls.engine, self.engine)
        self.assertFalse(self.controls.locked)
        self.assertEqual(self.controls.total_actions, 0)

    def test_execute_play(self):
        result = self.controls.execute(ControlAction.PLAY)
        self.assertTrue(result.get("success"))
        self.assertTrue(self.engine.started)

    def test_execute_pause(self):
        result = self.controls.execute(ControlAction.PAUSE)
        self.assertTrue(result.get("success"))

    def test_execute_stop(self):
        result = self.controls.execute(ControlAction.STOP)
        self.assertTrue(result.get("success"))
        self.assertTrue(self.engine.stopped)

    def test_execute_restart(self):
        result = self.controls.execute(ControlAction.RESTART)
        self.assertTrue(result.get("success"))

    def test_execute_speak(self):
        result = self.controls.execute(ControlAction.SPEAK, text="Hola")
        self.assertTrue(result.get("success"))
        self.assertIn("Hola", self.engine.spoken)

    def test_execute_speak_without_text(self):
        result = self.controls.execute(ControlAction.SPEAK)
        self.assertFalse(result.get("success"))

    def test_execute_set_gesture(self):
        result = self.controls.execute(ControlAction.SET_GESTURE, gesture="talking")
        self.assertTrue(result.get("success"))
        self.assertIn(GestureType.TALKING, self.engine.gestures)

    def test_execute_set_gesture_invalid(self):
        result = self.controls.execute(ControlAction.SET_GESTURE, gesture="nope")
        self.assertFalse(result.get("success"))

    def test_execute_start_recording(self):
        result = self.controls.execute(
            ControlAction.START_RECORDING, output_path="out.mp4"
        )
        self.assertTrue(result.get("success"))
        self.assertEqual(self.engine.recording_path, "out.mp4")

    def test_execute_stop_recording(self):
        result = self.controls.execute(ControlAction.STOP_RECORDING)
        self.assertTrue(result.get("success"))
        self.assertTrue(self.engine.recording_stopped)

    def test_execute_export_video(self):
        result = self.controls.execute(
            ControlAction.EXPORT_VIDEO, output_path="final.mp4"
        )
        self.assertTrue(result.get("success"))

    def test_execute_export_video_no_path(self):
        result = self.controls.execute(ControlAction.EXPORT_VIDEO)
        self.assertFalse(result.get("success"))

    def test_execute_mute_unmute(self):
        self.controls.execute(ControlAction.MUTE)
        self.assertTrue(self.engine.state.audio.muted)
        self.controls.execute(ControlAction.UNMUTE)
        self.assertFalse(self.engine.state.audio.muted)

    def test_execute_set_volume(self):
        result = self.controls.execute(ControlAction.SET_VOLUME, volume=0.5)
        self.assertTrue(result.get("success"))
        self.assertEqual(self.engine.state.audio.volume, 0.5)

    def test_execute_set_volume_clamps(self):
        self.controls.execute(ControlAction.SET_VOLUME, volume=5.0)
        self.assertEqual(self.engine.state.audio.volume, 1.0)

    def test_lock(self):
        self.controls.lock("test")
        result = self.controls.execute(ControlAction.PLAY)
        self.assertFalse(result.get("success"))
        self.controls.unlock()
        result = self.controls.execute(ControlAction.PLAY)
        self.assertTrue(result.get("success"))

    def test_register_callback(self):
        received = {"v": False}

        def cb(result):
            received["v"] = True

        self.controls.register_callback(ControlAction.PLAY, cb)
        self.controls.execute(ControlAction.PLAY)
        self.assertTrue(received["v"])

    def test_history(self):
        self.controls.execute(ControlAction.PLAY)
        self.controls.execute(ControlAction.STOP)
        hist = self.controls.get_history()
        self.assertEqual(len(hist), 2)
        self.assertEqual(self.controls.get_last_action()["action"], "stop")

    def test_get_info(self):
        info = self.controls.get_info()
        self.assertIn("engine_attached", info)
        self.assertIn("total_actions", info)

    def test_available_actions(self):
        actions = self.controls.get_available_actions()
        self.assertIn("play", actions)
        self.assertIn("speak", actions)


# ============================================================
# SETTINGS
# ============================================================

class TestSettingsController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.ensure_directories()
        self.tmpdir = Path(tempfile.mkdtemp())
        self.settings_path = self.tmpdir / "settings.json"
        self.settings = SettingsController(self.config)

    def tearDown(self):
        for f in self.tmpdir.glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            self.tmpdir.rmdir()
        except OSError:
            pass

    def test_initial(self):
        self.assertEqual(self.settings.current_profile, SettingsProfile.DEFAULT)
        self.assertFalse(self.settings.dirty)

    def test_get_default(self):
        fps = self.settings.get("render.fps")
        self.assertEqual(fps, DEFAULT_SETTINGS["render"]["fps"])

    def test_get_missing_returns_default(self):
        val = self.settings.get("nonexistent.key", "fallback")
        self.assertEqual(val, "fallback")

    def test_set_value(self):
        self.settings.set("render.fps", 60)
        self.assertEqual(self.settings.get("render.fps"), 60)
        self.assertTrue(self.settings.dirty)
        self.assertEqual(self.settings.total_changes, 1)

    def test_set_nested_new_key(self):
        self.settings.set("custom.section.key", 123)
        self.assertEqual(self.settings.get("custom.section.key"), 123)

    def test_update_multiple(self):
        self.settings.update({
            "render.fps": 45,
            "audio.tts_rate": 1.2,
        })
        self.assertEqual(self.settings.get("render.fps"), 45)
        self.assertEqual(self.settings.get("audio.tts_rate"), 1.2)

    def test_delete_key(self):
        self.settings.set("custom.test", 1)
        ok = self.settings.delete("custom.test")
        self.assertTrue(ok)
        self.assertIsNone(self.settings.get("custom.test"))

    def test_save_and_load(self):
        self.settings.set("render.fps", 50)
        self.assertTrue(self.settings.save(str(self.settings_path)))

        s2 = SettingsController(self.config)
        ok = s2.load(str(self.settings_path))
        self.assertTrue(ok)
        self.assertEqual(s2.get("render.fps"), 50)

    def test_load_nonexistent(self):
        s2 = SettingsController(self.config)
        ok = s2.load(str(self.tmpdir / "no_existe.json"))
        self.assertFalse(ok)

    def test_reset_section(self):
        self.settings.set("render.fps", 99)
        self.settings.reset("render")
        self.assertEqual(self.settings.get("render.fps"), DEFAULT_SETTINGS["render"]["fps"])

    def test_reset_all(self):
        self.settings.set("render.fps", 99)
        self.settings.set("audio.tts_rate", 2.0)
        self.settings.reset()
        self.assertEqual(self.settings.get("render.fps"), DEFAULT_SETTINGS["render"]["fps"])

    def test_apply_profile_performance(self):
        self.settings.apply_profile(SettingsProfile.PERFORMANCE)
        self.assertEqual(self.settings.current_profile, SettingsProfile.PERFORMANCE)
        self.assertEqual(self.settings.get("render.fps"), 60)

    def test_apply_profile_low_end(self):
        self.settings.apply_profile(SettingsProfile.LOW_END)
        self.assertEqual(self.settings.get("render.fps"), 24)

    def test_apply_profile_debug(self):
        self.settings.apply_profile(SettingsProfile.DEBUG)
        self.assertTrue(self.settings.get("debug.enabled"))

    def test_get_section(self):
        sec = self.settings.get_section("render")
        self.assertIn("fps", sec)
        self.assertIn("width", sec)

    def test_get_all(self):
        all_data = self.settings.get_all()
        self.assertIsInstance(all_data, dict)
        self.assertIn("render", all_data)

    def test_autosave(self):
        self.settings.enable_autosave(True, interval=5.0)
        self.assertTrue(self.settings.autosave_enabled)
        self.assertEqual(self.settings.autosave_interval, 5.0)

    def test_history(self):
        self.settings.set("render.fps", 55)
        hist = self.settings.get_history()
        self.assertGreater(len(hist), 0)

    def test_available_profiles(self):
        profiles = self.settings.get_available_profiles()
        self.assertIn("default", profiles)
        self.assertIn("performance", profiles)

    def test_get_info(self):
        info = self.settings.get_info()
        self.assertIn("profile", info)
        self.assertIn("dirty", info)
        self.assertIn("autosave", info)


# ============================================================
# PREVIEW
# ============================================================

class TestPreviewController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.preview = PreviewController(self.config)
        self.state = State()
        self.preview.initialize()

    def test_initial(self):
        self.assertEqual(self.preview.mode, PreviewMode.NORMAL)
        self.assertTrue(self.preview.enabled)
        self.assertTrue(self.preview.visible)

    def test_set_mode_debug(self):
        self.preview.set_mode(PreviewMode.DEBUG)
        self.assertEqual(self.preview.mode, PreviewMode.DEBUG)
        self.assertGreater(len(self.preview.overlays), 0)

    def test_set_mode_grid(self):
        self.preview.set_mode(PreviewMode.GRID)
        self.assertTrue(self.preview.grid_enabled)

    def test_cycle_mode(self):
        initial = self.preview.mode
        self.preview.cycle_mode()
        self.assertNotEqual(self.preview.mode, initial)

    def test_add_overlay(self):
        self.preview.clear_overlays()
        self.preview.add_overlay(OverlayType.SIGNALS)
        self.assertIn(OverlayType.SIGNALS, self.preview.overlays)

    def test_remove_overlay(self):
        self.preview.add_overlay(OverlayType.SIGNALS)
        self.preview.remove_overlay(OverlayType.SIGNALS)
        self.assertNotIn(OverlayType.SIGNALS, self.preview.overlays)

    def test_toggle_overlay(self):
        self.preview.add_overlay(OverlayType.STATE)
        self.preview.toggle_overlay(OverlayType.STATE)
        self.assertNotIn(OverlayType.STATE, self.preview.overlays)
        self.preview.toggle_overlay(OverlayType.STATE)
        self.assertIn(OverlayType.STATE, self.preview.overlays)

    def test_set_overlays(self):
        self.preview.set_overlays([OverlayType.FPS, OverlayType.FRAME])
        self.assertEqual(len(self.preview.overlays), 2)

    def test_set_resolution(self):
        self.preview.set_resolution(800, 600)
        self.assertEqual(self.preview.width, 800)
        self.assertEqual(self.preview.height, 600)

    def test_set_scale(self):
        self.preview.set_scale(2.0)
        self.assertEqual(self.preview.scale, 2.0)

    def test_set_scale_clamps(self):
        self.preview.set_scale(10.0)
        self.assertEqual(self.preview.scale, 4.0)

    def test_set_offset(self):
        self.preview.set_offset(10.0, -5.0)
        self.assertEqual(self.preview.offset_x, 10.0)
        self.assertEqual(self.preview.offset_y, -5.0)

    def test_reset_view(self):
        self.preview.set_scale(2.0)
        self.preview.set_offset(10.0, 10.0)
        self.preview.reset_view()
        self.assertEqual(self.preview.scale, 1.0)
        self.assertEqual(self.preview.offset_x, 0.0)

    def test_visibility(self):
        self.preview.hide()
        self.assertFalse(self.preview.visible)
        self.preview.show()
        self.assertTrue(self.preview.visible)
        self.preview.toggle_visibility()
        self.assertFalse(self.preview.visible)

    def test_update_writes_overlay_data(self):
        for _ in range(5):
            self.preview.update(0.016, self.state)
        data = self.preview.get_overlay_data()
        self.assertIn("fps", data)
        self.assertIn("engine_state", data)

    def test_capture_snapshot(self):
        self.preview.set_snapshot_interval(0.01)
        for _ in range(5):
            self.preview.update(0.05, self.state)
            time.sleep(0.01)
        snap = self.preview.get_last_snapshot()
        self.assertIsNotNone(snap)
        self.assertIn("frame", snap)

    def test_pause_resume(self):
        self.preview.pause()
        u0 = self.preview.updates
        self.preview.update(0.016, self.state)
        self.assertEqual(self.preview.updates, u0)
        self.preview.resume()
        self.preview.update(0.016, self.state)
        self.assertGreater(self.preview.updates, u0)

    def test_available_modes(self):
        modes = self.preview.get_available_modes()
        self.assertIn("normal", modes)
        self.assertIn("debug", modes)

    def test_available_overlays(self):
        overlays = self.preview.get_available_overlays()
        self.assertIn("fps", overlays)
        self.assertIn("signals", overlays)

    def test_get_info(self):
        info = self.preview.get_info()
        self.assertIn("mode", info)
        self.assertIn("canvas", info)
        self.assertIn("overlays", info)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)