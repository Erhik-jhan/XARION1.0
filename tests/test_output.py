# tests/test_output.py

import os
import sys
import time
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
from app.core.state import RecordingState

from app.output.recorder import Recorder, RecorderBackend
from app.output.video_export import (
    VideoExporter,
    ExportFormat,
    ExportQuality,
    QUALITY_PRESETS,
    CODECS,
)


# ============================================================
# RECORDER
# ============================================================

class TestRecorder(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.ensure_directories()
        self.tmpdir = Path(tempfile.mkdtemp())
        self.recorder = Recorder(self.config)
        self.recorder.initialize()

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
        self.assertFalse(self.recorder.is_recording())
        self.assertFalse(self.recorder.is_paused())
        self.assertEqual(self.recorder.state, RecordingState.INACTIVE)
        self.assertEqual(self.recorder.frame_count, 0)

    def test_backend_auto(self):
        self.assertIn(self.recorder.backend, (
            RecorderBackend.OPENCV,
            RecorderBackend.IMAGEIO,
            RecorderBackend.RAW,
        ))

    def test_start_stop(self):
        out = self.tmpdir / "test.mp4"
        ok = self.recorder.start(output_path=str(out))
        # Puede fallar si no hay cv2 ni imageio
        if ok:
            self.assertTrue(self.recorder.is_recording())
            self.assertEqual(self.recorder.state, RecordingState.RECORDING)
            time.sleep(0.05)
            duration = self.recorder.stop()
            self.assertGreaterEqual(duration, 0.0)
            self.assertFalse(self.recorder.is_recording())

    def test_start_twice_fails(self):
        out1 = self.tmpdir / "a.mp4"
        out2 = self.tmpdir / "b.mp4"
        ok1 = self.recorder.start(output_path=str(out1))
        if ok1:
            ok2 = self.recorder.start(output_path=str(out2))
            self.assertFalse(ok2)
            self.recorder.stop()

    def test_capture_frame_when_not_recording(self):
        # No debe lanzar excepcion
        self.recorder.capture_frame()

    def test_pause_resume(self):
        out = self.tmpdir / "p.mp4"
        ok = self.recorder.start(output_path=str(out))
        if ok:
            self.recorder.pause()
            self.assertTrue(self.recorder.is_paused())
            self.recorder.resume()
            self.assertFalse(self.recorder.is_paused())
            self.recorder.stop()

    def test_set_limits(self):
        self.recorder.set_limits(max_frames=100, max_duration=10.0)
        self.assertEqual(self.recorder.max_frames, 100)
        self.assertEqual(self.recorder.max_duration, 10.0)

    def test_set_codec(self):
        self.recorder.set_codec("avc1")
        self.assertEqual(self.recorder.codec, "avc1")

    def test_attach_detach_audio(self):
        self.recorder.attach_audio("audio.wav")
        self.assertEqual(self.recorder.audio_path, "audio.wav")
        self.assertTrue(self.recorder.audio_enabled)
        self.recorder.detach_audio()
        self.assertIsNone(self.recorder.audio_path)
        self.assertFalse(self.recorder.audio_enabled)

    def test_empty_frame(self):
        frame = self.recorder._empty_frame()
        self.assertIsNotNone(frame)

    def test_finalize_alias(self):
        out = self.tmpdir / "f.mp4"
        ok = self.recorder.start(output_path=str(out))
        if ok:
            duration = self.recorder.finalize()
            self.assertGreaterEqual(duration, 0.0)

    def test_get_info(self):
        info = self.recorder.get_info()
        self.assertIn("backend", info)
        self.assertIn("recording", info)
        self.assertIn("fps", info)
        self.assertIn("resolution", info)

    def test_raw_backend(self):
        self.recorder.set_backend(RecorderBackend.RAW)
        out = self.tmpdir / "raw.bin"
        ok = self.recorder.start(output_path=str(out))
        self.assertTrue(ok)
        self.recorder.capture_frame([[0, 0, 0], [0, 0, 0]])
        self.recorder.stop()
        self.assertEqual(self.recorder.backend, RecorderBackend.RAW)


# ============================================================
# VIDEO EXPORTER
# ============================================================

class TestVideoExporter(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.ensure_directories()
        self.tmpdir = Path(tempfile.mkdtemp())
        self.exporter = VideoExporter(self.config)
        self.exporter.initialize()

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
        self.assertEqual(self.exporter.format, ExportFormat.MP4)
        self.assertEqual(self.exporter.quality, ExportQuality.HIGH)
        self.assertEqual(self.exporter.total_exports, 0)

    def test_quality_presets(self):
        for q in ExportQuality:
            self.assertIn(q, QUALITY_PRESETS)
            self.assertIn("crf", QUALITY_PRESETS[q])
            self.assertIn("preset", QUALITY_PRESETS[q])

    def test_codecs(self):
        for f in ExportFormat:
            self.assertIn(f, CODECS)
            self.assertIn("video", CODECS[f])
            self.assertIn("audio", CODECS[f])

    def test_export_nonexistent(self):
        ok = self.exporter.export("no_existe.mp4")
        self.assertFalse(ok)
        self.assertGreater(self.exporter.total_failures, 0)

    def test_set_format(self):
        self.exporter.set_format(ExportFormat.WEBM)
        self.assertEqual(self.exporter.format, ExportFormat.WEBM)

    def test_set_quality(self):
        self.exporter.set_quality(ExportQuality.ULTRA)
        self.assertEqual(self.exporter.quality, ExportQuality.ULTRA)

    def test_set_fps(self):
        self.exporter.set_fps(60)
        self.assertEqual(self.exporter.fps, 60)

    def test_set_fps_clamps(self):
        self.exporter.set_fps(0)
        self.assertEqual(self.exporter.fps, 1)

    def test_set_resolution(self):
        self.exporter.set_resolution(800, 600)
        self.assertEqual(self.exporter.resolution, (800, 600))

    def test_set_resolution_clamps(self):
        self.exporter.set_resolution(1, 1)
        self.assertEqual(self.exporter.resolution, (16, 16))

    def test_set_audio(self):
        self.exporter.set_audio(True, audio_path="audio.wav")
        self.assertTrue(self.exporter.audio_enabled)
        self.assertEqual(self.exporter.audio_path, "audio.wav")

    def test_set_metadata(self):
        self.exporter.set_metadata("title", "Test")
        self.assertEqual(self.exporter.metadata["title"], "Test")

    def test_clear_metadata(self):
        self.exporter.set_metadata("title", "Test")
        self.exporter.clear_metadata()
        self.assertEqual(len(self.exporter.metadata), 0)

    def test_convert_alias(self):
        # Debe fallar en origen inexistente
        ok = self.exporter.convert(
            "no_existe.mp4", ExportFormat.WEBM
        )
        self.assertFalse(ok)

    def test_available_formats(self):
        fmts = self.exporter.get_available_formats()
        self.assertIn("mp4", fmts)
        self.assertIn("webm", fmts)

    def test_available_qualities(self):
        qs = self.exporter.get_available_qualities()
        self.assertIn("high", qs)
        self.assertIn("lossless", qs)

    def test_get_info(self):
        info = self.exporter.get_info()
        self.assertIn("format", info)
        self.assertIn("quality", info)
        self.assertIn("ffmpeg", info)

    def test_set_ffmpeg_path(self):
        self.exporter.set_ffmpeg_path("/usr/bin/ffmpeg")
        self.assertEqual(self.exporter.ffmpeg_path, "/usr/bin/ffmpeg")

    def test_export_copy_same_extension(self):
        # Crear archivo temporal para simular input
        src = self.tmpdir / "src.mp4"
        src.write_bytes(b"fake video data")

        dst = self.tmpdir / "dst.mp4"

        # Forzar backend sin ffmpeg para probar fallback
        self.exporter.ffmpeg_available = False

        ok = self.exporter.export(str(src), str(dst))
        # El fallback debe copiar si la extension es la misma
        if ok:
            self.assertTrue(dst.exists())


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)