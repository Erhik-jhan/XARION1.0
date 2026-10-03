# tests/test_avatar.py

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
from app.core.state import State, GestureType

from app.avatar.loader import AvatarLoader
from app.avatar.renderer import AvatarRenderer
from app.avatar.eyes import EyesController
from app.avatar.blink import BlinkController
from app.avatar.mouth import MouthController, Viseme, PHONEME_TO_VISEME, VISEME_PROFILES
from app.avatar.head_motion import HeadMotionController, HeadMotionMode
from app.avatar.body_motion import BodyMotionController, BodyMotionMode


# ============================================================
# LOADER
# ============================================================

class TestAvatarLoader(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.ensure_directories()
        self.loader = AvatarLoader(self.config)

    def test_initial_state(self):
        self.assertFalse(self.loader.is_loaded())
        self.assertIsNone(self.loader.avatar_path)
        self.assertIsNone(self.loader.avatar_format)

    def test_supported_formats(self):
        self.assertIn(".vrm", AvatarLoader.SUPPORTED_FORMATS)
        self.assertIn(".glb", AvatarLoader.SUPPORTED_FORMATS)
        self.assertIn(".png", AvatarLoader.SUPPORTED_FORMATS)
        self.assertIn(".model3.json", AvatarLoader.SUPPORTED_FORMATS)

    def test_list_available_empty_or_list(self):
        result = self.loader.list_available()
        self.assertIsInstance(result, list)

    def test_load_nonexistent(self):
        result = self.loader.load("no_existe_avatar.xyz")
        self.assertFalse(result.get("success"))

    def test_detect_format_live2d(self):
        p = Path("avatar.model3.json")
        fmt = self.loader._detect_format(p)
        self.assertEqual(fmt, "live2d")

    def test_detect_format_unknown(self):
        p = Path("avatar.unknown")
        fmt = self.loader._detect_format(p)
        self.assertIsNone(fmt)

    def test_unload(self):
        self.loader.unload()
        self.assertFalse(self.loader.is_loaded())


# ============================================================
# RENDERER
# ============================================================

class TestAvatarRenderer(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.renderer = AvatarRenderer(self.config)
        self.state = State()
        self.renderer.initialize()

    def test_initialization(self):
        self.assertTrue(self.renderer.initialized)
        self.assertIsNotNone(self.renderer.canvas)

    def test_render_without_avatar(self):
        # No debe lanzar excepcion
        self.renderer.render(0.016, self.state)
        self.assertEqual(self.renderer.frames_rendered, 0)

    def test_render_with_avatar(self):
        self.state.avatar_loaded = True
        self.renderer.render(0.016, self.state)
        self.assertEqual(self.renderer.frames_rendered, 1)

    def test_load_png_layers(self):
        avatar_data = {
            "path": "fake/avatar.png",
            "format": "png_layers",
            "raw": {
                "type": "png_layers",
                "base": "fake/avatar.png",
                "layers": {"body": "fake/body.png"},
                "loaded": True,
            },
            "metadata": {},
        }
        ok = self.renderer.load_layers(avatar_data)
        self.assertTrue(ok)
        self.assertIn("body", self.renderer.layers)

    def test_resize(self):
        self.renderer.resize(800, 600)
        self.assertEqual(self.renderer.width, 800)
        self.assertEqual(self.renderer.height, 600)

    def test_set_background(self):
        self.renderer.set_background((10, 20, 30, 255))
        self.assertEqual(self.renderer.background, (10, 20, 30, 255))

    def test_get_frame(self):
        self.state.avatar_loaded = True
        self.renderer.render(0.016, self.state)
        frame = self.renderer.get_frame()
        self.assertIsNotNone(frame)
        self.assertIn("canvas", frame)
        self.assertIn("layers", frame)

    def test_get_stats(self):
        stats = self.renderer.get_stats()
        self.assertIn("initialized", stats)
        self.assertIn("frames_rendered", stats)
        self.assertIn("resolution", stats)

    def test_shutdown(self):
        self.renderer.shutdown()
        self.assertFalse(self.renderer.initialized)


# ============================================================
# EYES
# ============================================================

class TestEyesController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.eyes = EyesController(self.config)
        self.state = State()
        self.eyes.initialize()

    def test_initial_values(self):
        self.assertEqual(self.eyes.look_x, 0.0)
        self.assertEqual(self.eyes.look_y, 0.0)
        self.assertEqual(self.eyes.openness, 1.0)

    def test_look_at(self):
        self.eyes.look_at(0.5, -0.5)
        self.assertEqual(self.eyes.target_look_x, 0.5)
        self.assertEqual(self.eyes.target_look_y, -0.5)

    def test_look_at_clamps(self):
        self.eyes.look_at(5.0, -5.0)
        self.assertEqual(self.eyes.target_look_x, 1.0)
        self.assertEqual(self.eyes.target_look_y, -1.0)

    def test_set_openness(self):
        self.eyes.set_openness(0.5)
        self.assertEqual(self.eyes.target_openness, 0.5)

    def test_set_dilation_clamps(self):
        self.eyes.set_dilation(5.0)
        self.assertEqual(self.eyes.target_dilation, 1.5)

    def test_set_color(self):
        self.eyes.set_color(255, 0, 0)
        self.assertEqual(self.eyes.color, (255, 0, 0))

    def test_update_writes_state(self):
        self.eyes.set_openness(0.5)
        for _ in range(60):
            self.eyes.update(0.016, self.state)
        self.assertGreaterEqual(self.state.avatar_components.eyes.openness, 0.3)
        self.assertLessEqual(self.state.avatar_components.eyes.openness, 0.7)

    def test_enable_follow(self):
        self.eyes.enable_follow(True)
        self.assertTrue(self.eyes.follow_target)
        self.eyes.enable_follow(False)
        self.assertFalse(self.eyes.follow_target)

    def test_get_state(self):
        s = self.eyes.get_state()
        self.assertIsNotNone(s)
        self.assertEqual(s.openness, self.eyes.openness)

    def test_get_info(self):
        info = self.eyes.get_info()
        self.assertIn("look", info)
        self.assertIn("openness", info)
        self.assertIn("color", info)


# ============================================================
# BLINK
# ============================================================

class TestBlinkController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.blink = BlinkController(self.config)
        self.state = State()
        self.blink.initialize()

    def test_initial(self):
        self.assertTrue(self.blink.enabled)
        self.assertFalse(self.blink.is_blinking)
        self.assertEqual(self.blink.blink_count, 0)

    def test_blink_now(self):
        self.blink.blink_now()
        self.assertTrue(self.blink.is_blinking)

    def test_update_advances_blink(self):
        self.blink.set_duration(0.05)
        self.blink.blink_now()
        for _ in range(10):
            self.blink.update(0.02, self.state)
            time.sleep(0.005)
        self.assertGreaterEqual(self.blink.blink_count, 1)

    def test_enable_disable(self):
        self.blink.enable(False)
        self.assertFalse(self.blink.enabled)
        self.blink.enable(True)
        self.assertTrue(self.blink.enabled)

    def test_set_interval(self):
        self.blink.set_interval(1.0, 2.0)
        self.assertEqual(self.blink.interval_min, 1.0)
        self.assertEqual(self.blink.interval_max, 2.0)

    def test_set_double_chance(self):
        self.blink.set_double_chance(0.5)
        self.assertEqual(self.blink.double_blink_chance, 0.5)

    def test_get_state(self):
        s = self.blink.get_state()
        self.assertIsNotNone(s)
        self.assertTrue(s.enabled)

    def test_get_info(self):
        info = self.blink.get_info()
        self.assertIn("enabled", info)
        self.assertIn("blink_count", info)


# ============================================================
# MOUTH
# ============================================================

class TestMouthController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.mouth = MouthController(self.config)
        self.state = State()
        self.mouth.initialize()

    def test_initial(self):
        self.assertEqual(self.mouth.current_viseme, Viseme.SILENCE)
        self.assertEqual(self.mouth.openness, 0.0)

    def test_set_viseme(self):
        self.mouth.set_viseme(Viseme.A)
        self.assertEqual(self.mouth.target_viseme, Viseme.A)

    def test_set_phoneme(self):
        self.mouth.set_phoneme("a")
        self.assertEqual(self.mouth.target_viseme, Viseme.A)

    def test_phoneme_mapping(self):
        self.assertIn("a", PHONEME_TO_VISEME)
        self.assertEqual(PHONEME_TO_VISEME["a"], Viseme.A)
        self.assertEqual(PHONEME_TO_VISEME["m"], Viseme.M)

    def test_viseme_profiles(self):
        for v in Viseme:
            self.assertIn(v, VISEME_PROFILES)
            profile = VISEME_PROFILES[v]
            self.assertIn("openness", profile)
            self.assertIn("smile", profile)
            self.assertIn("width", profile)

    def test_set_openness(self):
        self.mouth.set_openness(0.8)
        self.assertAlmostEqual(self.mouth.target_openness, 0.8, places=2)

    def test_set_smile(self):
        self.mouth.set_smile(0.9)
        self.assertAlmostEqual(self.mouth.target_smile, 0.9, places=2)

    def test_set_color(self):
        self.mouth.set_color(100, 200, 50)
        self.assertEqual(self.mouth.color, (100, 200, 50))

    def test_update_writes_state(self):
        self.mouth.set_viseme(Viseme.A)
        for _ in range(40):
            self.mouth.update(0.016, self.state)
        self.assertGreater(self.state.avatar_components.mouth.openness, 0.3)

    def test_set_text(self):
        self.mouth.set_text("hola")
        self.assertGreater(len(self.mouth.recent_visemes), 0)

    def test_get_available_visemes(self):
        visemes = self.mouth.get_available_visemes()
        self.assertIn("A", visemes)
        self.assertIn("silence", visemes)

    def test_get_info(self):
        info = self.mouth.get_info()
        self.assertIn("openness", info)
        self.assertIn("viseme", info)


# ============================================================
# HEAD
# ============================================================

class TestHeadMotionController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.head = HeadMotionController(self.config)
        self.state = State()
        self.head.initialize()

    def test_initial(self):
        self.assertEqual(self.head.mode, HeadMotionMode.IDLE)
        self.assertEqual(self.head.rotation_x, 0.0)

    def test_set_mode(self):
        self.head.set_mode(HeadMotionMode.TALKING)
        self.assertEqual(self.head.mode, HeadMotionMode.TALKING)
        self.assertEqual(self.head.mode_changes, 1)

    def test_nod(self):
        self.head.nod(count=2, duration=0.3)
        self.assertTrue(self.head._nod_active)
        self.assertEqual(self.head._nod_count, 2)

    def test_shake(self):
        self.head.shake(count=3, duration=0.3)
        self.assertTrue(self.head._shake_active)
        self.assertEqual(self.head._shake_count, 3)

    def test_look_at(self):
        self.head.look_at(0.5, -0.5)
        self.assertEqual(self.head.target_position["x"], 0.5)
        self.assertEqual(self.head.target_position["y"], -0.5)

    def test_set_rotation_clamps(self):
        self.head.set_rotation(5.0, 5.0, 5.0)
        self.assertLessEqual(abs(self.head.target_rotation_x), self.head.rot_limit_x)
        self.assertLessEqual(abs(self.head.target_rotation_y), self.head.rot_limit_y)
        self.assertLessEqual(abs(self.head.target_rotation_z), self.head.rot_limit_z)

    def test_update_writes_state(self):
        for _ in range(20):
            self.head.update(0.016, self.state)
        # El estado debe recibir valores
        self.assertIsInstance(self.state.avatar_components.head.rotation_x, float)

    def test_enable_voice_reactive(self):
        self.head.enable_voice_reactive(False)
        self.assertFalse(self.head.voice_reactive)

    def test_get_available_modes(self):
        modes = self.head.get_available_modes()
        self.assertIn("idle", modes)
        self.assertIn("talking", modes)

    def test_get_info(self):
        info = self.head.get_info()
        self.assertIn("mode", info)
        self.assertIn("rotation", info)


# ============================================================
# BODY
# ============================================================

class TestBodyMotionController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.body = BodyMotionController(self.config)
        self.state = State()
        self.body.initialize()

    def test_initial(self):
        self.assertEqual(self.body.mode, BodyMotionMode.IDLE)
        self.assertEqual(self.body.scale, 1.0)

    def test_set_mode(self):
        self.body.set_mode(BodyMotionMode.EXCITED)
        self.assertEqual(self.body.mode, BodyMotionMode.EXCITED)
        self.assertEqual(self.body.mode_changes, 1)

    def test_set_position_clamps(self):
        self.body.set_position(5.0, 5.0, 5.0)
        self.assertLessEqual(abs(self.body.target_position_x), self.body.pos_limit_x)
        self.assertLessEqual(abs(self.body.target_position_y), self.body.pos_limit_y)

    def test_set_scale_clamps(self):
        self.body.set_scale(5.0)
        self.assertLessEqual(self.body.target_scale, self.body.scale_max)
        self.body.set_scale(0.01)
        self.assertGreaterEqual(self.body.target_scale, self.body.scale_min)

    def test_trigger_beat(self):
        self.body.trigger_beat(0.8)
        self.assertAlmostEqual(self.body.beat_punch, 0.8, places=2)

    def test_update_writes_state(self):
        for _ in range(20):
            self.body.update(0.016, self.state)
        self.assertIsInstance(self.state.avatar_components.body.position_x, float)

    def test_set_lean(self):
        self.body.set_lean(0.05)
        self.assertAlmostEqual(self.body.target_lean, 0.05, places=3)

    def test_get_available_modes(self):
        modes = self.body.get_available_modes()
        self.assertIn("idle", modes)
        self.assertIn("excited", modes)

    def test_reset(self):
        self.body.set_mode(BodyMotionMode.EXCITED)
        self.body.reset()
        self.assertEqual(self.body.mode, BodyMotionMode.IDLE)
        self.assertEqual(self.body.position_x, 0.0)

    def test_get_info(self):
        info = self.body.get_info()
        self.assertIn("mode", info)
        self.assertIn("position", info)
        self.assertIn("scale", info)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)