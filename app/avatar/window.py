# app/avatar/window.py

import sys
import time
from pathlib import Path
from typing import Optional, Any

try:
    from PyQt6.QtCore import Qt, QTimer, QPoint
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QTransform, QImage
    from PyQt6.QtWidgets import QApplication, QWidget
    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False


class AvatarWindow:
    """
    Ventana sin bordes y con fondo transparente para mostrar el avatar.
    Se mantiene siempre al frente y permite arrastrarla con el raton.
    """

    def __init__(self, image_path: Optional[str] = None, fps: int = 30):
        if not PYQT_AVAILABLE:
            raise RuntimeError("PyQt6 no esta instalado")

        self.image_path = image_path
        self.fps = max(1, fps)
        self.app: Any = None
        self.widget: Any = None
        self.pixmap: Any = None
        self.timer: Any = None

        # Estado visual
        self.position_x = 0.0
        self.position_y = 0.0
        self.scale = 1.0
        self.rotation = 0.0
        self.opacity = 1.0
        self.glow_intensity = 1.0
        self.glow_color = QColor(0, 255, 100)

        # Ciclo
        self._running = False
        self._drag_offset = None
        self._last_tick = 0.0
        self._breath_phase = 0.0
        self._breath_amplitude = 0.008
        self._breath_speed = 0.9
        self._glow_phase = 0.0

        # Callbacks
        self.on_frame = None

    # =====================================================
    # CICLO
    # =====================================================

    def start(self):
        """Crea la ventana y arranca el bucle."""
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.widget = _AvatarWidget(self)
        self.widget.show()
        self._load_image()

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        interval = int(1000 / self.fps)
        self.timer.start(interval)

        self._running = True
        self._last_tick = time.time()
        self.app.exec()

    def stop(self):
        """Detiene la ventana."""
        self._running = False
        if self.timer is not None:
            self.timer.stop()
        if self.widget is not None:
            self.widget.close()
        if self.app is not None:
            self.app.quit()

    def _load_image(self):
        """Carga la imagen del avatar."""
        if not self.image_path:
            return
        p = Path(self.image_path)
        if not p.exists():
            print(f"[AvatarWindow] Imagen no encontrada: {p}")
            return
        self.pixmap = QPixmap(str(p))
        if self.pixmap.isNull():
            print(f"[AvatarWindow] Error cargando imagen: {p}")
            return
        self._resize_widget()
        print(f"[AvatarWindow] Avatar cargado: {p.name} ({self.pixmap.width()}x{self.pixmap.height()})")

    def _resize_widget(self):
        """Ajusta la ventana al tamano de la imagen."""
        if self.pixmap is None or self.widget is None:
            return
        w = int(self.pixmap.width() * self.scale)
        h = int(self.pixmap.height() * self.scale)
        self.widget.resize(w, h)
        self.widget.update()

    # =====================================================
    # TICK
    # =====================================================

    def _tick(self):
        """Actualiza el estado visual cada frame."""
        now = time.time()
        delta = max(0.0, now - self._last_tick)
        self._last_tick = now

        if not self._running:
            return

        # Respiracion (bobbing)
        self._breath_phase += delta * self._breath_speed * 6.28318
        self._glow_phase += delta * 1.5 * 6.28318

        # Callback externo (el motor puede actualizar cosas)
        if callable(self.on_frame):
            try:
                self.on_frame(delta)
            except Exception as e:
                print(f"[AvatarWindow] on_frame error: {e}")

        if self.widget is not None:
            self.widget.update()

    # =====================================================
    # PINTADO
    # =====================================================

    def paint(self, painter: Any):
        """Dibuja el avatar con las transformaciones actuales."""
        if self.pixmap is None:
            return

        # Offset vertical por respiracion
        import math
        breath_y = math.sin(self._breath_phase) * self._breath_amplitude * self.pixmap.height()

        # Centro del widget
        cw = self.widget.width() / 2.0
        ch = self.widget.height() / 2.0

        painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(painter.RenderHint.Antialiasing, True)

        painter.translate(cw, ch + breath_y)
        painter.rotate(self.rotation)
        painter.scale(self.scale, self.scale)
        painter.translate(-self.pixmap.width() / 2.0, -self.pixmap.height() / 2.0)

        painter.setOpacity(max(0.0, min(1.0, self.opacity)))
        painter.drawPixmap(0, 0, self.pixmap)

    # =====================================================
    # API PUBLICA
    # =====================================================

    def set_position(self, x: float, y: float):
        """Mueve la ventana a una posicion en pantalla."""
        if self.widget is not None:
            self.widget.move(int(x), int(y))

    def set_scale(self, scale: float):
        """Ajusta la escala del avatar."""
        self.scale = max(0.1, min(3.0, scale))
        self._resize_widget()

    def set_rotation(self, degrees: float):
        """Rota el avatar en grados."""
        self.rotation = degrees

    def set_opacity(self, opacity: float):
        """Ajusta la opacidad (0.0 a 1.0)."""
        self.opacity = max(0.0, min(1.0, opacity))

    def set_glow(self, intensity: float):
        """Ajusta la intensidad del glow (0.0 a 2.0)."""
        self.glow_intensity = max(0.0, min(2.0, intensity))

    def set_breathing(self, amplitude: float, speed: float):
        """Configura el bobbing (respiracion)."""
        self._breath_amplitude = max(0.0, min(0.1, amplitude))
        self._breath_speed = max(0.1, speed)

    def is_running(self) -> bool:
        return self._running


# =========================================================
# WIDGET INTERNO
# =========================================================

if PYQT_AVAILABLE:

    class _AvatarWidget(QWidget):
        """Widget sin bordes transparente."""

        def __init__(self, window: "AvatarWindow"):
            super().__init__()
            self._window = window
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
            self.resize(600, 600)

        def paintEvent(self, event):
            from PyQt6.QtGui import QPainter
            painter = QPainter(self)
            self._window.paint(painter)

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._window._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(self, event):
            if self._window._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self._window._drag_offset)
                event.accept()

        def mouseReleaseEvent(self, event):
            self._window._drag_offset = None

        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Escape:
                self._window.stop()
