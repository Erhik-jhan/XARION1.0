# app/avatar/loader.py

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.core.config import Config
from app.core.state import State, AvatarState


class AvatarLoader:
    """
    Cargador oficial de avatares de XARION-1.0.
    Soporta VRM, Live2D, GLB/GLTF, PNG por capas y formatos personalizados.
    """

    SUPPORTED_FORMATS = {
        ".vrm": "vrm",
        ".glb": "glb",
        ".gltf": "gltf",
        ".fbx": "fbx",
        ".live2d": "live2d",
        ".model3.json": "live2d",
        ".png": "png_layers",
        ".json": "custom",
    }

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.avatar_data: Optional[Dict[str, Any]] = None
        self.avatar_path: Optional[Path] = None
        self.avatar_format: Optional[str] = None
        self.raw_model: Any = None
        self.metadata: Dict[str, Any] = {}
        self.load_time: float = 0.0

    # =====================================================
    # CARGA PRINCIPAL
    # =====================================================

    def load(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Carga un avatar desde disco.
        Si no se especifica path, busca el avatar por defecto en assets/avatar/.
        """
        start = time.time()

        try:
            self.avatar_path = self._resolve_path(path)
            if self.avatar_path is None:
                return self._fail("No se encontró ningún avatar para cargar")

            self.avatar_format = self._detect_format(self.avatar_path)
            if self.avatar_format is None:
                return self._fail(f"Formato no soportado: {self.avatar_path.suffix}")

            self.raw_model = self._load_by_format(self.avatar_path, self.avatar_format)
            if self.raw_model is None:
                return self._fail("El archivo del avatar está vacío o corrupto")

            self.metadata = self._extract_metadata(self.avatar_path, self.avatar_format)
            self.avatar_data = {
                "path": str(self.avatar_path),
                "format": self.avatar_format,
                "raw": self.raw_model,
                "metadata": self.metadata,
            }

            self.load_time = time.time() - start

            return {
                "success": True,
                "path": str(self.avatar_path),
                "format": self.avatar_format,
                "metadata": self.metadata,
                "load_time": self.load_time,
            }

        except Exception as e:
            return self._fail(f"Excepción al cargar avatar: {e}")

    # =====================================================
    # RESOLUCIÓN DE PATH
    # =====================================================

    def _resolve_path(self, path: Optional[str]) -> Optional[Path]:
        """Resuelve la ruta del avatar (explícita o por defecto)."""
        if path:
            p = Path(path)
            if p.exists():
                return p
            alt = self.config.AVATAR_DIR / path
            if alt.exists():
                return alt
            return None

        # Buscar el primer archivo válido en assets/avatar/
        if not self.config.AVATAR_DIR.exists():
            return None

        for file in sorted(self.config.AVATAR_DIR.iterdir()):
            if file.is_file() and self._detect_format(file) is not None:
                return file

        return None

    # =====================================================
    # DETECCIÓN DE FORMATO
    # =====================================================

    def _detect_format(self, path: Path) -> Optional[str]:
        """Detecta el formato del avatar a partir de su extensión."""
        name = path.name.lower()

        if name.endswith(".model3.json"):
            return "live2d"

        suffix = path.suffix.lower()
        return self.SUPPORTED_FORMATS.get(suffix)

    # =====================================================
    # CARGA POR FORMATO
    # =====================================================

    def _load_by_format(self, path: Path, fmt: str) -> Any:
        """Despacha la carga según el formato detectado."""
        loaders = {
            "vrm": self._load_vrm,
            "glb": self._load_gltf,
            "gltf": self._load_gltf,
            "fbx": self._load_fbx,
            "live2d": self._load_live2d,
            "png_layers": self._load_png_layers,
            "custom": self._load_custom,
        }
        loader = loaders.get(fmt)
        if loader is None:
            return None
        return loader(path)

    def _load_vrm(self, path: Path) -> Dict[str, Any]:
        """Carga un archivo VRM (metadatos + referencia)."""
        return {
            "type": "vrm",
            "file": str(path),
            "size": path.stat().st_size,
            "loaded": True,
        }

    def _load_gltf(self, path: Path) -> Dict[str, Any]:
        """Carga un archivo GLB/GLTF."""
        return {
            "type": "gltf",
            "file": str(path),
            "size": path.stat().st_size,
            "loaded": True,
        }

    def _load_fbx(self, path: Path) -> Dict[str, Any]:
        """Carga un archivo FBX."""
        return {
            "type": "fbx",
            "file": str(path),
            "size": path.stat().st_size,
            "loaded": True,
        }

    def _load_live2d(self, path: Path) -> Dict[str, Any]:
        """Carga un modelo Live2D (model3.json + texturas)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "type": "live2d",
                "file": str(path),
                "model_data": data,
                "loaded": True,
            }
        except Exception:
            return None

    def _load_png_layers(self, path: Path) -> Dict[str, Any]:
        """Carga un avatar en capas PNG (ojos, boca, cuerpo, etc.)."""
        layers = {}
        base_dir = path.parent

        for layer_name in ["body", "eyes", "mouth", "head", "antenna"]:
            for ext in [".png", ".webp"]:
                candidate = base_dir / f"{layer_name}{ext}"
                if candidate.exists():
                    layers[layer_name] = str(candidate)
                    break

        return {
            "type": "png_layers",
            "base": str(path),
            "layers": layers,
            "loaded": True,
        }

    def _load_custom(self, path: Path) -> Dict[str, Any]:
        """Carga un avatar definido por un JSON personalizado."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "type": "custom",
                "file": str(path),
                "data": data,
                "loaded": True,
            }
        except Exception:
            return None

    # =====================================================
    # METADATOS
    # =====================================================

    def _extract_metadata(self, path: Path, fmt: str) -> Dict[str, Any]:
        """Extrae metadatos básicos del avatar."""
        meta = {
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "format": fmt,
            "loaded_at": time.time(),
        }

        if fmt == "live2d":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta["version"] = data.get("Version", "unknown")
                meta["textures"] = data.get("FileReferences", {}).get("Textures", [])
                meta["motions"] = list(
                    data.get("FileReferences", {}).get("Motions", {}).keys()
                )
                meta["expressions"] = [
                    e.get("Name") for e in data.get("FileReferences", {}).get("Expressions", [])
                ]
            except Exception:
                pass

        elif fmt == "custom":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta["name"] = data.get("name", "custom_avatar")
                meta["parts"] = list(data.get("parts", {}).keys())
            except Exception:
                pass

        elif fmt == "png_layers":
            meta["layers"] = list(self.raw_model.get("layers", {}).keys()) if self.raw_model else []

        return meta

    # =====================================================
    # CONSULTAS
    # =====================================================

    def is_loaded(self) -> bool:
        """Devuelve True si hay un avatar cargado."""
        return self.avatar_data is not None

    def get_model(self) -> Any:
        """Devuelve el modelo crudo cargado."""
        return self.raw_model

    def get_metadata(self) -> Dict[str, Any]:
        """Devuelve los metadatos del avatar."""
        return self.metadata

    def get_info(self) -> Dict[str, Any]:
        """Devuelve un resumen del estado del loader."""
        return {
            "loaded": self.is_loaded(),
            "path": str(self.avatar_path) if self.avatar_path else None,
            "format": self.avatar_format,
            "metadata": self.metadata,
            "load_time": self.load_time,
        }

    def unload(self):
        """Libera el avatar de memoria."""
        self.avatar_data = None
        self.avatar_path = None
        self.avatar_format = None
        self.raw_model = None
        self.metadata = {}
        self.load_time = 0.0

    # =====================================================
    # UTILIDADES
    # =====================================================

    def _fail(self, message: str) -> Dict[str, Any]:
        """Devuelve un resultado de error uniforme."""
        return {
            "success": False,
            "error": message,
            "path": None,
            "format": None,
        }

    def list_available(self) -> List[Dict[str, Any]]:
        """Lista todos los avatares disponibles en assets/avatar/."""
        results = []
        if not self.config.AVATAR_DIR.exists():
            return results

        for file in sorted(self.config.AVATAR_DIR.iterdir()):
            if file.is_file():
                fmt = self._detect_format(file)
                if fmt:
                    results.append({
                        "name": file.name,
                        "path": str(file),
                        "format": fmt,
                        "size": file.stat().st_size,
                    })
        return results