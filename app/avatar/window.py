# app/avatar/window.py

import sys
import time
from pathlib import Path
from typing import Optional, Any

try:
    from PyQt6.QtCore import Qt, QTimer, QPoint
    from PyQt6.QtGui import QPixmap, QPainter, QColor
    from PyQt6.QtWidgets import QApplication, QWidget
    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False

from app.avatar.renderer import AvatarRenderer


class AvatarWindow:
    """
    Ventana transparente sin bordes que muestra el avatar por capas.
    Se ajusta a un porcentaje del ancho de la pantalla y se mantiene
    siempre al frente. Arrastrable con el raton.
    """

    def __init__(
        self,
        renderer: Optional[AvatarRenderer] = None,
        screen_size_percent: int = 30,
        fps: int = 30,
    ):
        if not PYQT_AVAILABLE:
            raise RuntimeError("PyQt6 no esta instalado")

        self.renderer = renderer
        self.screen_size_percent = max(5, min(100, screen_size_percent))
        self.fps = max(1, fps)

        self.app: Any = None
        self.widget: Any = None
        self.timer: Any = None

        self._running = False
        self._drag_offset = None
        self._last_tick = 0.0

        # Escala calculada
        self.scale = 1.0
        self.base_size = (1678, 937)

        # Callbacks
        self.on_frame = None

    # =====================================================
    # CICLO
    # =====================================================

    def prepare(self):
        """Crea el widget y lo muestra, sin lanzar app.exec().
        Se usa cuando el motor controla el bucle principal con QTimer."""
        self.app = QApplication.instance() or QApplication(sys.argv)

        if self.renderer is not None:
            self.base_size = self.renderer.get_base_size()

        self._compute_scale()

        self.widget = _AvatarWidget(self)
        self.widget.show()
        self._running = True
        self._last_tick = time.time()
        print(f"[AvatarWindow] Ventana preparada ({self.widget.width()}x{self.widget.height()}, escala {self.scale:.2f})")
        return self.widget

    def tick(self, delta: float):
        """Avanza un frame desde fuera (QTimer del motor)."""
        if not self._running:
            return
        if callable(self.on_frame):
            try:
                self.on_frame(delta)
            except Exception as e:
                print(f"[AvatarWindow] on_frame error: {e}")
        if self.widget is not None:
            self.widget.update()

    def start(self):
        """Crea la ventana y arranca el bucle (modo autonomo)."""
        self.app = QApplication.instance() or QApplication(sys.argv)

        if self.renderer is not None:
            self.base_size = self.renderer.get_base_size()

        self._compute_scale()

        self.widget = _AvatarWidget(self)
        self.widget.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        interval = int(1000 / self.fps)
        self.timer.start(interval)

        self._running = True
        self._last_tick = time.time()
        print(f"[AvatarWindow] Ventana iniciada ({self.widget.width()}x{self.widget.height()}, escala {self.scale:.2f})")
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

    def _compute_scale(self):
        """Calcula la escala segun el porcentaje del ancho de pantalla."""
        screen = QApplication.primaryScreen()
        if screen is None:
            self.scale = 1.0
            return
        screen_w = screen.geometry().width()
        target_w = screen_w * (self.screen_size_percent / 100.0)
        base_w = self.base_size[0] or 1
        self.scale = target_w / base_w

    def _resize_widget(self):
        """Ajusta el widget al tamano escalado."""
        if self.widget is None:
            return
        w = int(self.base_size[0] * self.scale)
        h = int(self.base_size[1] * self.scale)
        self.widget.resize(w, h)

    # =====================================================
    # TICK
    # =====================================================

    def _tick(self):
        """Actualiza cada frame."""
        now = time.time()
        delta = max(0.0, now - self._last_tick)
        self._last_tick = now

        if not self._running:
            return

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

    def paint(self, painter: QPainter):
        """Delega el pintado al renderer."""
        if self.renderer is None or not self.renderer.loaded:
            return
        self.renderer.render(painter, scale=self.scale)

    # =====================================================
    # API PUBLICA
    # =====================================================

    def set_screen_size_percent(self, percent: int):
        """Ajusta el tamano en porcentaje del ancho de pantalla."""
        self.screen_size_percent = max(5, min(100, percent))
        self._compute_scale()
        self._resize_widget()

    def set_position(self, x: float, y: float):
        """Mueve la ventana."""
        if self.widget is not None:
            self.widget.move(int(x), int(y))

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
            self.setWindowTitle("XARION")
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

            # Forzar class para que Hyprland lo reconozca
            self.setProperty("class", "XARION")
            self.setProperty("app_id", "xarion")

            w = int(window.base_size[0] * window.scale)
            h = int(window.base_size[1] * window.scale)
            self.resize(w, h)

            # Posicion inicial: esquina inferior derecha
            screen = QApplication.primaryScreen()
            if screen is not None:
                geo = screen.geometry()
                x = geo.width() - w - 40
                y = geo.height() - h - 80
                self.move(int(x), int(y))

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
