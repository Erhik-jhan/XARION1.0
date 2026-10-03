# tests/test_audio.py

import os
import sys
import time
import wave
import struct
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
from app.core.state import State, AudioState, AudioFeatures

from app.audio.tts import TTSController, TTSEngine, DEFAULT_VOICES
from app.audio.audio_analyzer import AudioAnalyzer
from app.audio.volume import VolumeController
from app.audio.rhythm import RhythmController
from app.audio.synchronization import SynchronizationController, SyncMode


# ============================================================
# HELPERS
# ============================================================

def create_test_wav(path: Path, duration: float = 0.5, freq: float = 440.0, sr: int = 22050):
    """Genera un WAV de prueba con una senal senoidal."""
    import math
    n_samples = int(duration * sr)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = bytearray()
        for i in range(n_samples):
            val = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / sr))
            frames += struct.pack("<h", val)
        w.writeframes(bytes(frames))


# ============================================================
# TTS
# ============================================================

class TestTTSController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.ensure_directories()
        self.tts = TTSController(self.config)

    def test_initial(self):
        self.assertEqual(self.tts.engine, TTSEngine.EDGE)
        self.assertEqual(self.tts.language, "es")
        self.assertEqual(self.tts.rate, 1.0)
        self.assertEqual(self.tts.volume, 1.0)
        self.assertEqual(self.tts.total_synthesis, 0)

    def test_set_engine(self):
        self.tts.set_engine(TTSEngine.SYSTEM)
        self.assertEqual(self.tts.engine, TTSEngine.SYSTEM)

    def test_set_voice(self):
        self.tts.set_voice("test_voice")
        self.assertEqual(self.tts.voice, "test_voice")

    def test_set_language(self):
        self.tts.set_language("en")
        self.assertEqual(self.tts.language, "en")
        # Debe actualizar la voz por defecto
        self.assertIn("en", DEFAULT_VOICES[TTSEngine.EDGE])

    def test_set_rate_clamps(self):
        self.tts.set_rate(5.0)
        self.assertEqual(self.tts.rate, 2.0)
        self.tts.set_rate(0.1)
        self.assertEqual(self.tts.rate, 0.5)

    def test_set_pitch_clamps(self):
        self.tts.set_pitch(5.0)
        self.assertEqual(self.tts.pitch, 2.0)

    def test_set_volume_clamps(self):
        self.tts.set_volume(2.0)
        self.assertEqual(self.tts.volume, 1.0)

    def test_empty_text_fails(self):
        result = self.tts.synthesize("")
        self.assertFalse(result.get("success"))

    def test_available_engines(self):
        engines = self.tts.get_available_engines()
        self.assertIn("edge", engines)
        self.assertIn("system", engines)

    def test_register_custom_engine(self):
        class DummyEngine:
            pass
        self.tts.register_custom_engine("dummy", DummyEngine())
        self.assertIn("dummy", self.tts.get_available_engines())

    def test_clear_cache(self):
        self.tts.cache["x"] = {"success": True}
        self.tts.clear_cache()
        self.assertEqual(len(self.tts.cache), 0)

    def test_get_info(self):
        info = self.tts.get_info()
        self.assertIn("engine", info)
        self.assertIn("voice", info)
        self.assertIn("total_synthesis", info)


# ============================================================
# AUDIO ANALYZER
# ============================================================

class TestAudioAnalyzer(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.analyzer = AudioAnalyzer(self.config)
        self.analyzer.initialize()
        self.tmpdir = Path(tempfile.mkdtemp())
        self.wav_path = self.tmpdir / "test.wav"
        create_test_wav(self.wav_path, duration=0.3, freq=440.0)

    def tearDown(self):
        if self.wav_path.exists():
            self.wav_path.unlink()
        try:
            self.tmpdir.rmdir()
        except OSError:
            pass

    def test_initial(self):
        self.assertEqual(self.analyzer.current_sample, 0)
        self.assertIsInstance(self.analyzer.features, AudioFeatures)

    def test_load_wav(self):
        ok = self.analyzer.load(str(self.wav_path))
        self.assertTrue(ok)
        self.assertGreater(self.analyzer.total_samples, 0)
        self.assertGreater(self.analyzer.duration, 0.0)

    def test_load_nonexistent(self):
        ok = self.analyzer.load("no_existe.wav")
        self.assertFalse(ok)

    def test_analyze_chunk(self):
        self.analyzer.load(str(self.wav_path))
        features = self.analyzer.analyze()
        self.assertIsInstance(features, AudioFeatures)
        self.assertGreaterEqual(features.rms, 0.0)

    def test_analyze_advances(self):
        self.analyzer.load(str(self.wav_path))
        self.analyzer.set_chunk_size(256)
        f0 = self.analyzer.current_sample
        self.analyzer.analyze()
        self.assertGreater(self.analyzer.current_sample, f0)

    def test_reset_position(self):
        self.analyzer.load(str(self.wav_path))
        self.analyzer.analyze()
        self.analyzer.reset_position()
        self.assertEqual(self.analyzer.current_sample, 0)

    def test_seek(self):
        self.analyzer.load(str(self.wav_path))
        self.analyzer.seek(0.1)
        self.assertGreater(self.analyzer.current_sample, 0)

    def test_progress(self):
        self.analyzer.load(str(self.wav_path))
        p0 = self.analyzer.progress()
        self.analyzer.analyze()
        p1 = self.analyzer.progress()
        self.assertGreaterEqual(p1, p0)

    def test_get_waveform(self):
        self.analyzer.load(str(self.wav_path))
        wf = self.analyzer.get_waveform(64)
        self.assertIsInstance(wf, list)
        self.assertLessEqual(len(wf), 64)

    def test_get_info(self):
        self.analyzer.load(str(self.wav_path))
        info = self.analyzer.get_info()
        self.assertIn("backend", info)
        self.assertIn("sample_rate", info)
        self.assertIn("features", info)


# ============================================================
# VOLUME
# ============================================================

class TestVolumeController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.volume = VolumeController(self.config)
        self.volume.initialize()

    def test_initial(self):
        self.assertEqual(self.volume.master_volume, 1.0)
        self.assertEqual(self.volume.current_volume, 1.0)
        self.assertFalse(self.volume.muted)

    def test_set_master_volume(self):
        self.volume.set_master_volume(0.5)
        self.assertEqual(self.volume.master_volume, 0.5)
        self.assertEqual(self.volume.current_volume, 0.5)

    def test_set_master_volume_clamps(self):
        self.volume.set_master_volume(5.0)
        self.assertEqual(self.volume.master_volume, 1.0)
        self.volume.set_master_volume(-1.0)
        self.assertEqual(self.volume.master_volume, 0.0)

    def test_mute_unmute(self):
        self.volume.set_master_volume(0.7)
        self.volume.mute()
        self.assertTrue(self.volume.muted)
        self.assertEqual(self.volume.current_volume, 0.0)
        self.volume.unmute()
        self.assertFalse(self.volume.muted)
        self.assertEqual(self.volume.current_volume, 0.7)

    def test_toggle_mute(self):
        self.volume.toggle_mute()
        self.assertTrue(self.volume.muted)
        self.volume.toggle_mute()
        self.assertFalse(self.volume.muted)

    def test_set_db(self):
        self.volume.set_db(-6.0)
        self.assertLess(self.volume.master_volume, 1.0)

    def test_get_db(self):
        db = self.volume.get_db()
        self.assertLessEqual(db, 0.0)

    def test_apply_chunk(self):
        chunk = [0.5, 0.5, 0.5, 0.5]
        self.volume.set_master_volume(0.5)
        out = self.volume.apply(chunk)
        self.assertIsNotNone(out)

    def test_fade_to(self):
        self.volume.fade_to(0.5, duration=0.1)
        self.assertTrue(self.volume.fade_active)
        for _ in range(20):
            self.volume.update(0.02)
            time.sleep(0.005)
        self.assertFalse(self.volume.fade_active)

    def test_enable_limiter(self):
        self.volume.enable_limiter(True, threshold=0.9, ratio=3.0)
        self.assertTrue(self.volume.limiter_enabled)
        self.assertEqual(self.volume.limiter_threshold, 0.9)

    def test_enable_normalization(self):
        self.volume.enable_normalization(True, target_db=-3.0)
        self.assertTrue(self.volume.normalization_enabled)

    def test_get_info(self):
        info = self.volume.get_info()
        self.assertIn("master_volume", info)
        self.assertIn("muted", info)
        self.assertIn("limiter", info)


# ============================================================
# RHYTHM
# ============================================================

class TestRhythmController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.rhythm = RhythmController(self.config)
        self.rhythm.initialize()

    def test_initial(self):
        self.assertEqual(self.rhythm.bpm, 0.0)
        self.assertEqual(self.rhythm.total_beats, 0)

    def test_update_with_no_features(self):
        self.rhythm.update(0.016, None)
        self.assertEqual(self.rhythm.updates, 1)

    def test_update_with_features(self):
        f = AudioFeatures(rms=0.5, beat_detected=False)
        self.rhythm.update(0.016, f)
        self.assertGreater(self.rhythm.energy_level, 0.0)

    def test_register_beat(self):
        f = AudioFeatures(rms=0.9, beat_detected=True, beat_strength=0.8)
        self.rhythm.update(0.016, f)
        self.assertGreaterEqual(self.rhythm.total_beats, 1)
        self.assertGreater(self.rhythm.beat_punch, 0.0)

    def test_bpm_update(self):
        f = AudioFeatures(rhythm_bpm=120.0)
        self.rhythm.update(0.016, f)
        self.assertGreater(self.rhythm.bpm, 0.0)

    def test_set_bpm_range(self):
        self.rhythm.set_bpm_range(60.0, 180.0)
        self.assertEqual(self.rhythm.bpm_min, 60.0)
        self.assertEqual(self.rhythm.bpm_max, 180.0)

    def test_set_beats_per_bar(self):
        self.rhythm.set_beats_per_bar(4)
        self.assertEqual(self.rhythm.beats_per_bar, 4)

    def test_enable_prediction(self):
        self.rhythm.enable_prediction(False)
        self.assertFalse(self.rhythm.prediction_enabled)
        self.assertEqual(self.rhythm.next_beat_time, 0.0)

    def test_get_rhythm_intensity(self):
        intensity = self.rhythm.get_rhythm_intensity()
        self.assertGreaterEqual(intensity, 0.0)
        self.assertLessEqual(intensity, 1.0)

    def test_get_history(self):
        h = self.rhythm.get_history()
        self.assertIn("energy", h)
        self.assertIn("beat_strengths", h)

    def test_get_info(self):
        info = self.rhythm.get_info()
        self.assertIn("bpm", info)
        self.assertIn("total_beats", info)
        self.assertIn("prediction", info)


# ============================================================
# SYNCHRONIZATION
# ============================================================

class TestSynchronizationController(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.sync = SynchronizationController(self.config)
        self.sync.initialize()
        self.state = State()

    def test_initial(self):
        self.assertEqual(self.sync.mode, SyncMode.FULL)
        self.assertEqual(self.sync.lip_signal, 0.0)

    def test_set_mode(self):
        self.sync.set_mode(SyncMode.LIPSYNC)
        self.assertEqual(self.sync.mode, SyncMode.LIPSYNC)
        self.assertEqual(self.sync.head_weight, 0.0)

    def test_set_latency(self):
        self.sync.set_latency(0.1)
        self.assertEqual(self.sync.latency_compensation, 0.1)

    def test_set_weights(self):
        self.sync.set_weights(lip=0.9, head=0.4, body=0.3)
        self.assertEqual(self.sync.lip_weight, 0.9)
        self.assertEqual(self.sync.head_weight, 0.4)
        self.assertEqual(self.sync.body_weight, 0.3)

    def test_push_features(self):
        f = AudioFeatures(rms=0.5)
        self.sync.push_features(0.0, f)
        self.assertEqual(len(self.sync.audio_buffer), 1)

    def test_push_features_buffer_limit(self):
        for i in range(20):
            f = AudioFeatures(rms=0.5)
            self.sync.push_features(float(i), f)
        self.assertLessEqual(len(self.sync.audio_buffer), self.sync.buffer_size)

    def test_update_no_audio(self):
        self.sync.update(0.016, self.state)
        self.assertEqual(self.sync.updates, 1)

    def test_update_with_audio(self):
        self.state.audio.state = AudioState.PLAYING
        self.state.audio.current_time = 0.0
        f = AudioFeatures(rms=0.7, pitch=200.0, beat_strength=0.5)
        self.sync.push_features(0.0, f)
        self.sync.update(0.016, self.state)
        self.assertGreater(self.sync.lip_signal, 0.0)

    def test_get_signals(self):
        signals = self.sync.get_signals()
        self.assertIn("lip", signals)
        self.assertIn("head", signals)
        self.assertIn("body", signals)

    def test_available_modes(self):
        modes = self.sync.get_available_modes()
        self.assertIn("full", modes)
        self.assertIn("lipsync", modes)

    def test_get_info(self):
        info = self.sync.get_info()
        self.assertIn("mode", info)
        self.assertIn("signals", info)
        self.assertIn("weights", info)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)