# tests/test_core.py

import os
import sys
import time
import unittest
from pathlib import Path

# ------------------------------------------------------------
# Asegurar que la raiz este en el path
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import Config
from app.core.state import (
    State,
    EngineState,
    AvatarState,
    AudioState,
    MotionState,
    GestureType,
    RecordingState,
    EyesState,
    BlinkState,
    MouthState,
    HeadMotionState,
    BodyMotionState,
    AntennaState,
    AvatarComponents,
    AudioFeatures,
    AudioStateData,
    MotionStateData,
    GestureState,
    RecordingStateData,
)
from app.core.engine import XarionEngine


# ============================================================
# CONFIG
# ============================================================

class TestConfig(unittest.TestCase):

    def setUp(self):
        self.config = Config()

    def test_project_metadata(self):
        self.assertEqual(self.config.PROJECT_NAME, "XARION")
        self.assertEqual(self.config.VERSION, "1.0")

    def test_base_paths_exist(self):
        self.assertTrue(self.config.BASE_DIR.exists())
        self.assertIsInstance(self.config.ASSETS_DIR, Path)
        self.assertIsInstance(self.config.OUTPUT_DIR, Path)

    def test_ensure_directories(self):
        self.config.ensure_directories()
        self.assertTrue(self.config.OUTPUT_DIR.exists())
        self.assertTrue(self.config.CONFIG_DIR.exists())
        self.assertTrue(self.config.AVATAR_DIR.exists())
        self.assertTrue(self.config.VOICES_DIR.exists())

    def test_to_dict(self):
        data = self.config.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["PROJECT_NAME"], "XARION")
        self.assertEqual(data["VERSION"], "1.0")
        self.assertIn("FPS", data)
        self.assertIn("SAMPLE_RATE", data)

    def test_render_defaults(self):
        self.assertGreater(self.config.FPS, 0)
        self.assertGreater(self.config.WINDOW_WIDTH, 0)
        self.assertGreater(self.config.WINDOW_HEIGHT, 0)

    def test_audio_defaults(self):
        self.assertGreater(self.config.SAMPLE_RATE, 0)
        self.assertGreater(self.config.AUDIO_CHANNELS, 0)
        self.assertGreater(self.config.AUDIO_CHUNK_SIZE, 0)


# ============================================================
# STATE — SUBCOMPONENTES
# ============================================================

class TestStateComponents(unittest.TestCase):

    def test_eyes_defaults(self):
        eyes = EyesState()
        self.assertEqual(eyes.look_x, 0.0)
        self.assertEqual(eyes.look_y, 0.0)
        self.assertEqual(eyes.openness, 1.0)
        self.assertEqual(eyes.pupil_dilation, 1.0)

    def test_blink_defaults(self):
        blink = BlinkState()
        self.assertTrue(blink.enabled)
        self.assertFalse(blink.is_blinking)
        self.assertEqual(blink.blink_progress, 0.0)
        self.assertGreater(blink.interval_min, 0.0)
        self.assertGreater(blink.interval_max, blink.interval_min)

    def test_mouth_defaults(self):
        mouth = MouthState()
        self.assertEqual(mouth.openness, 0.0)
        self.assertGreaterEqual(mouth.smile, 0.0)
        self.assertLessEqual(mouth.smile, 1.0)
        self.assertEqual(mouth.viseme, "neutral")

    def test_head_defaults(self):
        head = HeadMotionState()
        self.assertEqual(head.rotation_x, 0.0)
        self.assertEqual(head.rotation_y, 0.0)
        self.assertEqual(head.rotation_z, 0.0)
        self.assertIn("x", head.target_position)
        self.assertIn("y", head.target_position)

    def test_body_defaults(self):
        body = BodyMotionState()
        self.assertEqual(body.position_x, 0.0)
        self.assertEqual(body.scale, 1.0)
        self.assertGreater(body.breathing_amplitude, 0.0)

    def test_antenna_defaults(self):
        antenna = AntennaState()
        self.assertEqual(antenna.glow_intensity, 1.0)
        self.assertGreater(antenna.pulse_speed, 0.0)

    def test_avatar_components(self):
        comps = AvatarComponents()
        self.assertIsInstance(comps.eyes, EyesState)
        self.assertIsInstance(comps.blink, BlinkState)
        self.assertIsInstance(comps.mouth, MouthState)
        self.assertIsInstance(comps.head, HeadMotionState)
        self.assertIsInstance(comps.body, BodyMotionState)
        self.assertIsInstance(comps.antenna, AntennaState)


# ============================================================
# STATE — AUDIO
# ============================================================

class TestAudioState(unittest.TestCase):

    def test_audio_features_defaults(self):
        f = AudioFeatures()
        self.assertEqual(f.rms, 0.0)
        self.assertEqual(f.db, -60.0)
        self.assertFalse(f.beat_detected)
        self.assertFalse(f.is_speech)
        self.assertEqual(f.phoneme, "neutral")

    def test_audio_state_data(self):
        a = AudioStateData()
        self.assertEqual(a.state, AudioState.EMPTY)
        self.assertIsNone(a.file_path)
        self.assertEqual(a.volume, 1.0)
        self.assertFalse(a.muted)
        self.assertIsInstance(a.features, AudioFeatures)

    def test_audio_features_bands(self):
        f = AudioFeatures()
        self.assertEqual(f.energy_band_low, 0.0)
        self.assertEqual(f.energy_band_mid, 0.0)
        self.assertEqual(f.energy_band_high, 0.0)


# ============================================================
# STATE — MOTION / GESTURE / RECORDING
# ============================================================

class TestMotionGestureRecording(unittest.TestCase):

    def test_motion_state_data(self):
        m = MotionStateData()
        self.assertEqual(m.state, MotionState.IDLE)
        self.assertTrue(m.idle_enabled)
        self.assertTrue(m.voice_driven_enabled)
        self.assertGreater(m.smoothing_factor, 0.0)

    def test_gesture_state(self):
        g = GestureState()
        self.assertEqual(g.current, GestureType.NEUTRAL)
        self.assertEqual(g.previous, GestureType.NEUTRAL)
        self.assertEqual(g.transition_progress, 1.0)
        self.assertTrue(g.auto_detect)

    def test_recording_state_data(self):
        r = RecordingStateData()
        self.assertEqual(r.state, RecordingState.INACTIVE)
        self.assertIsNone(r.output_path)
        self.assertEqual(r.frame_count, 0)
        self.assertGreater(r.fps, 0)
        self.assertEqual(len(r.resolution), 2)


# ============================================================
# STATE — PRINCIPAL
# ============================================================

class TestMainState(unittest.TestCase):

    def setUp(self):
        self.state = State()

    def test_initial_state(self):
        self.assertEqual(self.state.engine_state, EngineState.IDLE)
        self.assertFalse(self.state.is_running)
        self.assertIsNone(self.state.last_error)
        self.assertEqual(self.state.avatar_state, AvatarState.UNLOADED)
        self.assertFalse(self.state.avatar_loaded)

    def test_set_error(self):
        self.state.set_error("test error")
        self.assertEqual(self.state.engine_state, EngineState.ERROR)
        self.assertEqual(self.state.last_error, "test error")
        self.assertEqual(len(self.state.error_history), 1)

    def test_reset_error(self):
        self.state.set_error("test")
        self.state.reset_error()
        self.assertIsNone(self.state.last_error)
        self.assertEqual(self.state.engine_state, EngineState.IDLE)

    def test_set_avatar_loaded(self):
        self.state.set_avatar_loaded("path/to/avatar.png", "png_layers")
        self.assertTrue(self.state.avatar_loaded)
        self.assertEqual(self.state.avatar_path, "path/to/avatar.png")
        self.assertEqual(self.state.avatar_format, "png_layers")
        self.assertEqual(self.state.avatar_state, AvatarState.LOADED)

    def test_unload_avatar(self):
        self.state.set_avatar_loaded("path", "vrm")
        self.state.unload_avatar()
        self.assertFalse(self.state.avatar_loaded)
        self.assertIsNone(self.state.avatar_path)
        self.assertEqual(self.state.avatar_state, AvatarState.UNLOADED)

    def test_start_audio(self):
        self.state.start_audio(path="audio.wav", duration=3.5)
        self.assertEqual(self.state.audio.state, AudioState.PLAYING)
        self.assertEqual(self.state.audio.file_path, "audio.wav")
        self.assertEqual(self.state.audio.duration, 3.5)

    def test_pause_audio(self):
        self.state.start_audio()
        self.state.pause_audio()
        self.assertEqual(self.state.audio.state, AudioState.PAUSED)

    def test_stop_audio(self):
        self.state.start_audio()
        self.state.stop_audio()
        self.assertEqual(self.state.audio.state, AudioState.FINISHED)

    def test_change_gesture(self):
        self.state.change_gesture(GestureType.TALKING)
        self.assertEqual(self.state.gesture.current, GestureType.TALKING)
        self.assertEqual(self.state.gesture.previous, GestureType.NEUTRAL)

    def test_tick(self):
        f0 = self.state.frame_index
        self.state.tick(0.033)
        self.assertEqual(self.state.frame_index, f0 + 1)
        self.assertAlmostEqual(self.state.delta_time, 0.033, places=3)
        self.assertGreater(self.state.elapsed_time, 0.0)

    def test_start_and_stop_recording(self):
        self.state.start_recording("output.mp4", fps=30)
        self.assertEqual(self.state.recording.state, RecordingState.RECORDING)
        self.assertEqual(self.state.engine_state, EngineState.RECORDING)

        time.sleep(0.05)

        duration = self.state.stop_recording()
        self.assertGreaterEqual(duration, 0.0)
        self.assertEqual(self.state.recording.state, RecordingState.SAVED)
        self.assertEqual(self.state.engine_state, EngineState.READY)

    def test_increment_frame(self):
        self.state.start_recording("out.mp4")
        self.state.increment_frame()
        self.state.increment_frame()
        self.assertEqual(self.state.recording.frame_count, 2)

    def test_to_dict(self):
        data = self.state.to_dict()
        self.assertIsInstance(data, dict)
        self.assertIn("engine", data)
        self.assertIn("avatar", data)
        self.assertIn("audio", data)
        self.assertIn("motion", data)
        self.assertIn("gesture", data)
        self.assertIn("recording", data)
        self.assertIn("timing", data)

    def test_reset(self):
        self.state.set_error("test")
        self.state.set_avatar_loaded("x", "png")
        self.state.reset()
        self.assertEqual(self.state.engine_state, EngineState.IDLE)
        self.assertFalse(self.state.avatar_loaded)


# ============================================================
# ENGINE
# ============================================================

class TestEngine(unittest.TestCase):

    def setUp(self):
        self.engine = XarionEngine(Config())

    def test_engine_initialization(self):
        self.assertIsNotNone(self.engine.config)
        self.assertIsNotNone(self.engine.state)
        self.assertEqual(self.engine.state.engine_state, EngineState.IDLE)

    def test_register_module(self):
        class Dummy:
            pass
        dummy = Dummy()
        self.engine.register("dummy_module", dummy)
        self.assertIs(self.engine.dummy_module, dummy)

    def test_emit_without_callback(self):
        # No debe lanzar excepcion
        self.engine.emit("nonexistent_event")

    def test_on_and_emit(self):
        received = {}

        def callback(value):
            received["value"] = value

        self.engine.on("test_event", callback)
        self.engine.emit("test_event", 42)
        self.assertEqual(received["value"], 42)

    def test_status(self):
        status = self.engine.status()
        self.assertIsInstance(status, dict)
        self.assertIn("engine_state", status)
        self.assertIn("avatar_state", status)
        self.assertIn("audio_state", status)
        self.assertIn("motion_state", status)
        self.assertIn("recording_state", status)
        self.assertIn("frame_index", status)
        self.assertIn("fps", status)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)