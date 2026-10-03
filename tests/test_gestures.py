# tests/test_gestures.py

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
from app.core.state import State, GestureType, AudioFeatures

from app.gestures.neutral import NeutralGesture, NeutralVariant, NEUTRAL_VARIANTS
from app.gestures.question import QuestionGesture, QuestionVariant, QUESTION_VARIANTS
from app.gestures.talking import TalkingGesture, TalkingVariant, TALKING_VARIANTS


# ============================================================
# NEUTRAL GESTURE
# ============================================================

class TestNeutralGesture(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.gesture = NeutralGesture(self.config)
        self.state = State()
        self.gesture.initialize()

    def test_initial(self):
        self.assertEqual(self.gesture.gesture_type, GestureType.NEUTRAL)
        self.assertEqual(self.gesture.variant, NeutralVariant.BASE)
        self.assertTrue(self.gesture.active)

    def test_set_variant(self):
        self.gesture.set_variant(NeutralVariant.FRIENDLY)
        self.assertEqual(self.gesture.variant, NeutralVariant.FRIENDLY)
        self.assertEqual(self.gesture.target_smile, NEUTRAL_VARIANTS[NeutralVariant.FRIENDLY]["smile"])

    def test_set_intensity(self):
        self.gesture.set_intensity(0.5)
        self.assertEqual(self.gesture.intensity, 0.5)

    def test_set_intensity_clamps(self):
        self.gesture.set_intensity(5.0)
        self.assertEqual(self.gesture.intensity, 1.0)

    def test_update_writes_state(self):
        for _ in range(40):
            self.gesture.update(0.016, self.state)
        self.assertEqual(self.gesture.updates, 40)

    def test_override_pose(self):
        self.gesture.override_pose(smile=0.9, head_pitch=0.1)
        self.assertEqual(self.gesture.target_smile, 0.9)
        self.assertEqual(self.gesture.target_head_pitch, 0.1)

    def test_activate_deactivate(self):
        self.gesture.deactivate()
        self.assertFalse(self.gesture.active)
        self.gesture.activate()
        self.assertTrue(self.gesture.active)
        self.assertEqual(self.gesture.activations, 1)

    def test_get_pose(self):
        pose = self.gesture.get_pose()
        self.assertIn("head_pitch", pose)
        self.assertIn("smile", pose)

    def test_available_variants(self):
        variants = self.gesture.get_available_variants()
        self.assertIn("base", variants)
        self.assertIn("friendly", variants)

    def test_get_info(self):
        info = self.gesture.get_info()
        self.assertIn("variant", info)
        self.assertIn("pose", info)
        self.assertIn("transition", info)

    def test_reset(self):
        self.gesture.set_variant(NeutralVariant.FRIENDLY)
        self.gesture.reset()
        self.assertEqual(self.gesture.variant, NeutralVariant.BASE)


# ============================================================
# QUESTION GESTURE
# ============================================================

class TestQuestionGesture(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.gesture = QuestionGesture(self.config)
        self.state = State()
        self.gesture.initialize()

    def test_initial(self):
        self.assertEqual(self.gesture.gesture_type, GestureType.QUESTION)
        self.assertEqual(self.gesture.variant, QuestionVariant.NEUTRAL)
        self.assertFalse(self.gesture.active)

    def test_activate(self):
        self.gesture.activate(hold_duration=1.0)
        self.assertTrue(self.gesture.active)
        self.assertEqual(self.gesture.phase, "enter")
        self.assertEqual(self.gesture.hold_duration, 1.0)
        self.assertEqual(self.gesture.activations, 1)

    def test_phase_enter_to_hold(self):
        self.gesture.activate(hold_duration=0.1)
        for _ in range(20):
            self.gesture.update(0.05, self.state)
        self.assertIn(self.gesture.phase, ("hold", "exit", "idle"))

    def test_phase_hold_to_exit(self):
        self.gesture.activate(hold_duration=0.05)
        for _ in range(40):
            self.gesture.update(0.05, self.state)
        # Debe haber completado el ciclo
        self.assertIn(self.gesture.phase, ("exit", "idle"))

    def test_full_cycle_completes(self):
        self.gesture.activate(hold_duration=0.02)
        for _ in range(100):
            self.gesture.update(0.05, self.state)
        self.assertEqual(self.gesture.completions, 1)

    def test_set_variant(self):
        self.gesture.set_variant(QuestionVariant.SURPRISED)
        self.assertEqual(self.gesture.variant, QuestionVariant.SURPRISED)

    def test_set_intensity_clamps(self):
        self.gesture.set_intensity(5.0)
        self.assertEqual(self.gesture.intensity, 1.0)

    def test_set_hold_duration(self):
        self.gesture.set_hold_duration(2.0)
        self.assertEqual(self.gesture.hold_duration, 2.0)

    def test_set_auto_exit(self):
        self.gesture.set_auto_exit(False)
        self.assertFalse(self.gesture.auto_exit)

    def test_on_finish_callback(self):
        called = {"v": False}

        def cb():
            called["v"] = True

        self.gesture.on_finish(cb)
        self.gesture.activate(hold_duration=0.02)
        for _ in range(100):
            self.gesture.update(0.05, self.state)
        self.assertTrue(called["v"])

    def test_get_pose(self):
        pose = self.gesture.get_pose()
        self.assertIn("head_pitch", pose)
        self.assertIn("antenna_glow", pose)

    def test_available_variants(self):
        variants = self.gesture.get_available_variants()
        self.assertIn("neutral", variants)
        self.assertIn("curious", variants)

    def test_get_info(self):
        info = self.gesture.get_info()
        self.assertIn("variant", info)
        self.assertIn("phase", info)
        self.assertIn("hold", info)

    def test_reset(self):
        self.gesture.set_variant(QuestionVariant.CURIOUS)
        self.gesture.reset()
        self.assertEqual(self.gesture.variant, QuestionVariant.NEUTRAL)


# ============================================================
# TALKING GESTURE
# ============================================================

class TestTalkingGesture(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.gesture = TalkingGesture(self.config)
        self.state = State()
        self.gesture.initialize()

    def test_initial(self):
        self.assertEqual(self.gesture.gesture_type, GestureType.TALKING)
        self.assertEqual(self.gesture.variant, TalkingVariant.NORMAL)
        self.assertFalse(self.gesture.active)

    def test_activate(self):
        self.gesture.activate()
        self.assertTrue(self.gesture.active)
        self.assertEqual(self.gesture.activations, 1)

    def test_deactivate(self):
        self.gesture.activate()
        self.gesture.deactivate()
        self.assertFalse(self.gesture.active)

    def test_set_variant(self):
        self.gesture.set_variant(TalkingVariant.ENTHUSIASTIC)
        self.assertEqual(self.gesture.variant, TalkingVariant.ENTHUSIASTIC)

    def test_update_with_audio(self):
        self.gesture.activate()
        self.state.audio.features = AudioFeatures(rms=0.5, pitch=200.0)
        for _ in range(20):
            self.gesture.update(0.016, self.state)
        self.assertGreater(self.gesture.rms_smoothed, 0.0)

    def test_update_writes_state(self):
        self.gesture.activate()
        self.state.audio.features = AudioFeatures(rms=0.6, beat_strength=0.5)
        for _ in range(20):
            self.gesture.update(0.016, self.state)
        self.assertEqual(self.gesture.updates, 20)

    def test_silence_auto_exit(self):
        self.gesture.activate()
        self.gesture.set_auto_exit(True, silence_timeout=0.05, silence_threshold=0.05)
        self.state.audio.features = AudioFeatures(rms=0.0)
        for _ in range(50):
            self.gesture.update(0.05, self.state)
        self.assertEqual(self.gesture.completions, 1)

    def test_manual_nod(self):
        self.gesture.activate()
        self.gesture._start_nod()
        self.assertTrue(self.gesture.nod_active)
        self.assertGreater(self.gesture.total_nods, 0)

    def test_set_intensity_clamps(self):
        self.gesture.set_intensity(5.0)
        self.assertEqual(self.gesture.intensity, 1.0)

    def test_set_nod_chance(self):
        self.gesture.set_nod_chance(0.5)
        self.assertEqual(self.gesture.nod_chance, 0.5)

    def test_set_smoothing(self):
        self.gesture.set_smoothing(rms=0.1, pitch=0.1)
        self.assertEqual(self.gesture.rms_smoothing, 0.1)
        self.assertEqual(self.gesture.pitch_smoothing, 0.1)

    def test_on_finish_callback(self):
        called = {"v": False}

        def cb():
            called["v"] = True

        self.gesture.on_finish(cb)
        self.gesture.activate()
        self.gesture.set_auto_exit(True, silence_timeout=0.02, silence_threshold=0.1)
        self.state.audio.features = AudioFeatures(rms=0.0)
        for _ in range(100):
            self.gesture.update(0.05, self.state)
        self.assertTrue(called["v"])

    def test_get_signals(self):
        signals = self.gesture.get_signals()
        self.assertIn("rms", signals)
        self.assertIn("pitch", signals)
        self.assertIn("energy", signals)
        self.assertIn("beat", signals)

    def test_available_variants(self):
        variants = self.gesture.get_available_variants()
        self.assertIn("normal", variants)
        self.assertIn("enthusiastic", variants)

    def test_get_info(self):
        info = self.gesture.get_info()
        self.assertIn("variant", info)
        self.assertIn("signals", info)
        self.assertIn("nodding", info)

    def test_reset(self):
        self.gesture.set_variant(TalkingVariant.EXCITED)
        self.gesture.reset()
        self.assertEqual(self.gesture.variant, TalkingVariant.NORMAL)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
    