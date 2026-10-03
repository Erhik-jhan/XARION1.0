# tests/test_motion.py

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
from app.core.state import State, AudioFeatures, MotionState

from app.motion.motion_engine import MotionEngine, MotionMode, MOTION_MODE_PROFILES
from app.motion.smoothing import SmoothingController, SmoothingType
from app.motion.idle_motion import IdleMotionController, IdleMode, IDLE_MODE_PROFILES
from app.motion.voice_motion import VoiceMotionController, VoiceMotionMode, VOICE_MODE_PROFILES


# ============================================================
# MOTION ENGINE
# ============================================================

class TestMotionEngine(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.engine = MotionEngine(self.config)
        self.state = State()
        self.engine.initialize()

    def test_initial(self):
        self.assertEqual(self.engine.mode, MotionMode.COMBINED)
        self.assertEqual(self.engine.combined_signal, 0.0)

    def test_set_mode(self):
        self.engine.set_mode(MotionMode.VOICE)
        self.assertEqual(self.engine.mode, MotionMode.VOICE)
        self.assertEqual(self.engine.mode_changes, 1)

    def test_set_mode_same_no_change(self):
        self.engine.set_mode(MotionMode.COMBINED)
        self.assertEqual(self.engine.mode_changes, 0)

    def test_set_intensity(self):
        self.engine.set_intensity(1.5)
        self.assertEqual(self.engine.intensity, 1.5)

    def test_set_intensity_clamps(self):
        self.engine.set_intensity(10.0)
        self.assertEqual(self.engine.intensity, self.engine.intensity_max)
        self.engine.set_intensity(-5.0)
        self.assertEqual(self.engine.intensity, self.engine.intensity_min)

    def test_set_weights(self):
        self.engine.set_weights(head=0.5, body=0.3, mouth=0.2)
        self.assertEqual(self.engine.head_weight, 0.5)
        self.assertEqual(self.engine.body_weight, 0.3)
        self.assertEqual(self.engine.mouth_weight, 0.2)

    def test_trigger_gesture(self):
        self.engine.trigger_gesture(0.7)
        self.assertAlmostEqual(self.engine.gesture_signal, 0.7, places=2)

    def test_update_idle(self):
        for _ in range(30):
            self.engine.update(0.016, self.state)
        self.assertEqual(self.engine.updates, 30)
        self.assertGreater(self.engine.idle_signal, 0.0)

    def test_update_with_voice(self):
        self.state.audio.state = type(self.state.audio.state).PLAYING
        self.state.audio.features = AudioFeatures(rms=0.5, pitch=200.0)
        for _ in range(20):
            self.engine.update(0.016, self.state)
        self.assertGreater(self.engine.voice_signal, 0.0)

    def test_update_with_beat(self):
        self.state.audio.state = type(self.state.audio.state).PLAYING
        self.state.audio.features = AudioFeatures(beat_detected=True, beat_strength=0.8)
        self.engine.update(0.016, self.state)
        self.assertGreater(self.engine.rhythm_punch, 0.0)

    def test_register_submodule(self):
        class Dummy:
            def update(self, delta, state):
                pass
        dummy = Dummy()
        self.engine.register("smoothing", dummy)
        self.assertIs(self.engine.smoothing_controller, dummy)

    def test_get_signals(self):
        signals = self.engine.get_signals()
        self.assertIn("idle", signals)
        self.assertIn("voice", signals)
        self.assertIn("rhythm", signals)
        self.assertIn("gesture", signals)
        self.assertIn("combined", signals)

    def test_available_modes(self):
        modes = self.engine.get_available_modes()
        self.assertIn("idle", modes)
        self.assertIn("combined", modes)

    def test_reset(self):
        self.engine.set_mode(MotionMode.VOICE)
        self.engine.reset()
        self.assertEqual(self.engine.mode, MotionMode.COMBINED)

    def test_get_info(self):
        info = self.engine.get_info()
        self.assertIn("mode", info)
        self.assertIn("signals", info)
        self.assertIn("weights", info)


# ============================================================
# SMOOTHING
# ============================================================

class TestSmoothingController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.smoothing = SmoothingController(self.config)
        self.state = State()
        self.smoothing.initialize()

    def test_initial(self):
        self.assertEqual(self.smoothing.type, SmoothingType.EXPONENTIAL)

    def test_set_type(self):
        self.smoothing.set_type(SmoothingType.SPRING)
        self.assertEqual(self.smoothing.type, SmoothingType.SPRING)

    def test_set_factor(self):
        self.smoothing.set_factor(0.2)
        self.assertEqual(self.smoothing.factor, 0.2)

    def test_set_factor_clamps(self):
        self.smoothing.set_factor(5.0)
        self.assertEqual(self.smoothing.factor, 1.0)

    def test_set_factors(self):
        self.smoothing.set_factors(position=0.1, rotation=0.2, scale=0.3)
        self.assertEqual(self.smoothing.position_factor, 0.1)
        self.assertEqual(self.smoothing.rotation_factor, 0.2)
        self.assertEqual(self.smoothing.scale_factor, 0.3)

    def test_set_spring_params(self):
        self.smoothing.set_spring_params(stiffness=100.0, damping=10.0, mass=1.5)
        self.assertEqual(self.smoothing.spring_stiffness, 100.0)
        self.assertEqual(self.smoothing.spring_damping, 10.0)
        self.assertEqual(self.smoothing.spring_mass, 1.5)

    def test_update_writes_state(self):
        self.state.avatar_components.head.rotation_x = 0.5
        self.state.avatar_components.body.position_x = 0.5
        for _ in range(10):
            self.smoothing.update(0.016, self.state)
        # El estado debe haberse modificado
        self.assertNotEqual(self.state.avatar_components.head.rotation_x, 0.5)

    def test_spring_no_crash(self):
        self.smoothing.set_type(SmoothingType.SPRING)
        for _ in range(30):
            self.smoothing.update(0.016, self.state)
        self.assertEqual(self.smoothing.updates, 30)

    def test_critical_damp(self):
        self.smoothing.set_type(SmoothingType.CRITICAL_DAMP)
        for _ in range(30):
            self.smoothing.update(0.016, self.state)
        self.assertEqual(self.smoothing.updates, 30)

    def test_get_history(self):
        self.smoothing.update(0.016, self.state)
        hist = self.smoothing.get_history("head.rx")
        self.assertIsInstance(hist, list)

    def test_available_types(self):
        types = self.smoothing.get_available_types()
        self.assertIn("exponential", types)
        self.assertIn("spring", types)

    def test_get_info(self):
        info = self.smoothing.get_info()
        self.assertIn("type", info)
        self.assertIn("factors", info)
        self.assertIn("spring", info)


# ============================================================
# IDLE MOTION
# ============================================================

class TestIdleMotionController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.idle = IdleMotionController(self.config)
        self.state = State()
        self.idle.initialize()

    def test_initial(self):
        self.assertEqual(self.idle.mode, IdleMode.CALM)
        self.assertTrue(self.idle.enabled)

    def test_set_mode(self):
        self.idle.set_mode(IdleMode.ENERGETIC)
        self.assertEqual(self.idle.mode, IdleMode.ENERGETIC)
        self.assertGreater(self.idle.breath_amp, 0.0)

    def test_set_intensity(self):
        self.idle.set_intensity(1.5)
        self.assertEqual(self.idle.intensity, 1.5)

    def test_set_intensity_clamps(self):
        self.idle.set_intensity(5.0)
        self.assertEqual(self.idle.intensity, 2.0)

    def test_set_look_interval(self):
        self.idle.set_look_interval(1.0, 3.0)
        self.assertEqual(self.idle.look_interval_min, 1.0)
        self.assertEqual(self.idle.look_interval_max, 3.0)

    def test_set_look_amplitude(self):
        self.idle.set_look_amplitude(0.3)
        self.assertEqual(self.idle.look_amplitude, 0.3)

    def test_update_writes_state(self):
        for _ in range(30):
            self.idle.update(0.016, self.state)
        self.assertEqual(self.idle.updates, 30)
        # El cuerpo debe tener respiracion aplicada
        self.assertGreater(self.state.avatar_components.body.breathing_amplitude, 0.0)

    def test_suspend_resume(self):
        self.idle.suspend()
        self.assertTrue(self.idle.suspended)
        u0 = self.idle.updates
        self.idle.update(0.016, self.state)
        self.assertEqual(self.idle.updates, u0)  # No actualiza
        self.idle.resume()
        self.assertFalse(self.idle.suspended)

    def test_enable(self):
        self.idle.enable(False)
        self.assertFalse(self.idle.enabled)
        self.idle.enable(True)
        self.assertTrue(self.idle.enabled)

    def test_available_modes(self):
        modes = self.idle.get_available_modes()
        self.assertIn("calm", modes)
        self.assertIn("energetic", modes)

    def test_get_info(self):
        info = self.idle.get_info()
        self.assertIn("mode", info)
        self.assertIn("phases", info)
        self.assertIn("params", info)


# ============================================================
# VOICE MOTION
# ============================================================

class TestVoiceMotionController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.voice = VoiceMotionController(self.config)
        self.state = State()
        self.voice.initialize()

    def test_initial(self):
        self.assertEqual(self.voice.mode, VoiceMotionMode.NATURAL)
        self.assertTrue(self.voice.enabled)

    def test_set_mode(self):
        self.voice.set_mode(VoiceMotionMode.EXPRESSIVE)
        self.assertEqual(self.voice.mode, VoiceMotionMode.EXPRESSIVE)
        self.assertGreater(self.voice.head_amplitude, 0.0)

    def test_set_intensity(self):
        self.voice.set_intensity(1.2)
        self.assertEqual(self.voice.intensity, 1.2)

    def test_set_intensity_clamps(self):
        self.voice.set_intensity(5.0)
        self.assertEqual(self.voice.intensity, 2.0)

    def test_update_no_audio_decays(self):
        for _ in range(20):
            self.voice.update(0.016, self.state)
        self.assertEqual(self.voice.updates, 20)

    def test_update_with_audio(self):
        self.state.audio.state = type(self.state.audio.state).PLAYING
        self.state.audio.features = AudioFeatures(rms=0.6, pitch=200.0)
        for _ in range(20):
            self.voice.update(0.016, self.state)
        self.assertGreater(self.voice.rms_smoothed, 0.0)

    def test_set_speeds(self):
        self.voice.set_head_speed(2.0)
        self.voice.set_body_speed(1.5)
        self.assertEqual(self.voice.head_speed, 2.0)
        self.assertEqual(self.voice.body_speed, 1.5)

    def test_set_attack_release(self):
        self.voice.set_attack_release(attack=0.02, release=0.2)
        self.assertEqual(self.voice.attack_time, 0.02)
        self.assertEqual(self.voice.release_time, 0.2)

    def test_set_smoothing(self):
        self.voice.set_smoothing(rms=0.15, pitch=0.15)
        self.assertEqual(self.voice.rms_smoothing, 0.15)
        self.assertEqual(self.voice.pitch_smoothing, 0.15)

    def test_suspend_resume(self):
        self.voice.suspend()
        self.assertTrue(self.voice.suspended)
        u0 = self.voice.updates
        self.voice.update(0.016, self.state)
        self.assertEqual(self.voice.updates, u0)
        self.voice.resume()
        self.assertFalse(self.voice.suspended)

    def test_get_signals(self):
        signals = self.voice.get_signals()
        self.assertIn("rms", signals)
        self.assertIn("pitch", signals)
        self.assertIn("energy", signals)
        self.assertIn("beat", signals)

    def test_available_modes(self):
        modes = self.voice.get_available_modes()
        self.assertIn("natural", modes)
        self.assertIn("expressive", modes)

    def test_get_info(self):
        info = self.voice.get_info()
        self.assertIn("mode", info)
        self.assertIn("signals", info)
        self.assertIn("amplitudes", info)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)