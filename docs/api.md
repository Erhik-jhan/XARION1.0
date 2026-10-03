cat > docs/api.md << 'XARION_EOF'
# Referencia de API de XARION 1.0

Referencia de clases y modulos publicos del sistema.

## Indice de modulos

- [app.core.config](#appcoreconfig)
- [app.core.state](#appcorestate)
- [app.core.engine](#appcoreengine)
- [app.avatar.loader](#appavatarloader)
- [app.avatar.renderer](#appavatarrenderer)
- [app.avatar.eyes](#appavataeyes)
- [app.avatar.blink](#appavatablink)
- [app.avatar.mouth](#appavatarmouth)
- [app.avatar.head_motion](#appavatarhead_motion)
- [app.avatar.body_motion](#appavatarhead_motion)
- [app.audio.tts](#appaudiotts)
- [app.audio.audio_analyzer](#appaudioaudio_analyzer)
- [app.audio.volume](#appaudiovolume)
- [app.audio.rhythm](#appaudiorhythm)
- [app.audio.synchronization](#appaudiosynchronization)
- [app.motion.motion_engine](#appmotionmotion_engine)
- [app.motion.smoothing](#appmotionsmoothing)
- [app.motion.idle_motion](#appmotionidle_motion)
- [app.motion.voice_motion](#appmotionvoice_motion)
- [app.gestures.neutral](#appgesturesneutral)
- [app.gestures.question](#appgesturesquestion)
- [app.gestures.talking](#appgesturestalking)
- [app.interface.controls](#appinterfacecontrols)
- [app.interface.settings](#appinterfacesettings)
- [app.interface.preview](#appinterfacepreview)
- [app.output.recorder](#appoutputrecorder)
- [app.output.video_export](#appoutputvideo_export)

---

## app.core.config

### class Config

Configuracion global del sistema.

**Atributos principales:**

- `PROJECT_NAME: str = "XARION"`
- `VERSION: str = "1.0"`
- `BASE_DIR: Path`
- `ASSETS_DIR: Path`
- `OUTPUT_DIR: Path`
- `FPS: int = 30`
- `WINDOW_WIDTH: int = 1280`
- `WINDOW_HEIGHT: int = 720`
- `SAMPLE_RATE: int = 22050`
- `SMOOTHING_FACTOR: float = 0.15`

**Metodos:**

- `ensure_directories() -> None`: Crea las carpetas necesarias.
- `to_dict() -> Dict[str, Any]`: Devuelve la configuracion como dict.

---

## app.core.state

### Enum EngineState

Estados del motor: `IDLE`, `LOADING`, `READY`, `TALKING`, `RECORDING`, `ERROR`, `STOPPED`.

### Enum AvatarState

Estados del avatar: `UNLOADED`, `LOADING`, `LOADED`, `VISIBLE`, `HIDDEN`, `ERROR`.

### Enum AudioState

Estados del audio: `EMPTY`, `LOADING`, `READY`, `PLAYING`, `PAUSED`, `FINISHED`, `ERROR`.

### Enum MotionState

Estados del movimiento: `DISABLED`, `IDLE`, `ACTIVE`, `VOICE_DRIVEN`, `GESTURE`.

### Enum GestureType

Gestos disponibles: `NEUTRAL`, `QUESTION`, `TALKING`.

### Enum RecordingState

Estados de grabacion: `INACTIVE`, `PREPARING`, `RECORDING`, `PAUSING`, `FINISHING`, `SAVED`, `ERROR`.

### class EyesState

Sub-estado de ojos: `look_x`, `look_y`, `pupil_dilation`, `openness`, `glow_intensity`, `color`.

### class BlinkState

Sub-estado de parpadeo: `enabled`, `interval_min`, `interval_max`, `is_blinking`, `blink_progress`, `blink_duration`, `double_blink_chance`.

### class MouthState

Sub-estado de boca: `openness`, `smile`, `viseme`, `glow_intensity`, `color`.

### class HeadMotionState

Sub-estado de cabeza: `rotation_x`, `rotation_y`, `rotation_z`, `tilt_offset`, `nod_speed`, `follow_audio`, `follow_target`, `target_position`.

### class BodyMotionState

Sub-estado de cuerpo: `position_x`, `position_y`, `position_z`, `rotation_x`, `rotation_y`, `rotation_z`, `scale`, `breathing_phase`, `breathing_amplitude`, `sway_phase`.

### class AntennaState

Sub-estado de antena: `glow_intensity`, `pulse_phase`, `pulse_speed`, `color`.

### class AudioFeatures

Features de audio: `rms`, `db`, `pitch`, `spectral_centroid`, `zero_crossing_rate`, `beat_detected`, `beat_strength`, `rhythm_bpm`, `is_speech`, `phoneme`, `energy_band_low`, `energy_band_mid`, `energy_band_high`.

### class State

Estado global.

**Metodos principales:**

- `tick(delta)`: Avanza un frame.
- `set_error(message)`: Establece un error.
- `reset_error()`: Limpia el error.
- `set_avatar_loaded(path, fmt)`: Marca el avatar como cargado.
- `unload_avatar()`: Descarga el avatar.
- `start_audio(path, duration)`: Inicia reproduccion.
- `pause_audio()` / `stop_audio()`: Control de audio.
- `change_gesture(gesture, duration)`: Cambia de gesto.
- `start_recording(path, fps)`: Inicia grabacion.
- `stop_recording() -> float`: Detiene y devuelve duracion.
- `increment_frame()`: Suma un frame.
- `to_dict() -> Dict`: Serializa el estado.
- `reset()`: Reinicia todo.

---

## app.core.engine

### class XarionEngine

Motor central.

**Metodos:**

- `register(name, module)`: Registra un modulo.
- `on(event, callback)`: Registra un callback.
- `emit(event, *args)`: Dispara un evento.
- `initialize()`: Inicializa el motor.
- `start()`: Arranca el bucle.
- `stop()`: Detiene el motor.
- `speak(text, voice)`: TTS + gesto de habla.
- `set_gesture(gesture)`: Cambia gesto.
- `start_recording(path)`: Inicia grabacion.
- `stop_recording() -> float`: Detiene grabacion.
- `export_video(path) -> bool`: Exporta.
- `status() -> Dict`: Estado del motor.

---

## app.avatar.loader

### class AvatarLoader

Cargador de avatares.

**Constantes:**

- `SUPPORTED_FORMATS: Dict[str, str]`

**Metodos:**

- `load(path=None) -> Dict`: Carga un avatar.
- `is_loaded() -> bool`: Estado de carga.
- `get_model() -> Any`: Devuelve el modelo crudo.
- `get_metadata() -> Dict`: Metadatos.
- `get_info() -> Dict`: Info del loader.
- `unload()`: Libera memoria.
- `list_available() -> List[Dict]`: Avatares disponibles.

---

## app.avatar.renderer

### class AvatarRenderer

Renderizador por capas.

**Metodos:**

- `initialize()`: Prepara el canvas.
- `load_layers(avatar_data) -> bool`: Carga capas.
- `render(delta, state)`: Renderiza un frame.
- `get_frame() -> Any`: Devuelve el frame actual.
- `resize(width, height)`: Redimensiona.
- `set_background(color)`: Fondo.
- `get_stats() -> Dict`: Estadisticas.
- `shutdown()`: Libera recursos.

---

## app.avatar.eyes

### class EyesController

Controlador de ojos.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `look_at(x, y)`: Mira a un punto normalizado.
- `look_at_center()`: Vuelve al centro.
- `set_openness(value)`: Apertura 0.0 a 1.0.
- `set_dilation(value)`: Dilatacion 0.5 a 1.5.
- `set_glow(intensity)`: Brillo.
- `set_color(r, g, b)`: Color.
- `enable_follow(enabled)`: Seguimiento.
- `set_target_position(x, y)`: Objetivo.
- `enable_saccades(enabled)`: Micro-movimientos.
- `set_smoothing(value)`: Suavizado.
- `get_state() -> EyesState`: Estado.
- `get_info() -> Dict`: Info.

---

## app.avatar.blink

### class BlinkController

Controlador de parpadeo.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `blink_now()`: Fuerza parpadeo.
- `double_blink()`: Fuerza doble parpadeo.
- `enable(enabled)`: Activa/desactiva.
- `set_interval(min_s, max_s)`: Rango.
- `set_duration(duration)`: Duracion.
- `set_double_chance(chance)`: Probabilidad doble.
- `get_state() -> BlinkState`: Estado.
- `get_info() -> Dict`: Info.

---

## app.avatar.mouth

### class MouthController

Controlador de boca.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `set_viseme(viseme, duration)`: Cambia visema.
- `set_phoneme(phoneme)`: Fonema a visema.
- `set_text(text)`: Texto a secuencia de visemas.
- `set_openness(value)`: Apertura.
- `set_smile(value)`: Sonrisa.
- `set_width(value)`: Ancho.
- `set_glow(intensity)`: Brillo.
- `set_color(r, g, b)`: Color.
- `set_mode(mode)`: Modo (auto, audio, text, manual).
- `enable_coarticulation(enabled)`: Coarticulacion.
- `reset()`: Reinicia.
- `get_state() -> MouthState`: Estado.
- `get_info() -> Dict`: Info.

### Enum Viseme

Visemas: `SILENCE`, `A`, `E`, `I`, `O`, `U`, `M`, `F`, `S`, `L`, `R`, `TH`, `NEUTRAL`.

---

## app.avatar.head_motion

### class HeadMotionController

Controlador de cabeza.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `set_mode(mode)`: Cambia modo.
- `nod(count, duration)`: Asiente.
- `shake(count, duration)`: Niega.
- `look_at(x, y)`: Mira a objetivo.
- `enable_follow(enabled, strength)`: Seguimiento.
- `set_rotation(x, y, z, instant)`: Rotaciones.
- `set_tilt(offset)`: Inclinacion.
- `set_smoothing(value)`: Suavizado.
- `enable_voice_reactive(enabled, scale)`: Reaccion a voz.
- `enable_micro_motion(enabled, amplitude)`: Micro-movimientos.
- `get_state() -> HeadMotionState`: Estado.
- `get_info() -> Dict`: Info.

### Enum HeadMotionMode

Modos: `IDLE`, `TALKING`, `LISTENING`, `THINKING`, `NODDING`, `SHAKING`, `LOOKING`, `SURPRISED`.

---

## app.avatar.body_motion

### class BodyMotionController

Controlador de cuerpo.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `set_mode(mode)`: Cambia modo.
- `set_position(x, y, z, instant)`: Posicion.
- `set_rotation(x, y, z, instant)`: Rotacion.
- `set_scale(value, instant)`: Escala.
- `set_lean(value)`: Inclinacion.
- `set_smoothing(...)`: Suavizado.
- `enable_voice_reactive(enabled, scale)`: Voz.
- `enable_beat_reactive(enabled)`: Beats.
- `enable_micro_motion(enabled, amplitude)`: Micro.
- `get_state() -> BodyMotionState`: Estado.
- `get_info() -> Dict`: Info.

### Enum BodyMotionMode

Modos: `IDLE`, `TALKING`, `LISTENING`, `THINKING`, `EMPHASIS`, `EXCITED`, `TIRED`, `SURPRISED`, `RECORDING`.

---

## app.audio.tts

### class TTSController

Sintesis de voz multi-motor.

**Metodos:**

- `initialize()`: Inicializa motor.
- `synthesize(text, voice, language, output_path) -> Dict`: Sintetiza.
- `set_engine(engine, **kwargs)`: Cambia motor.
- `set_voice(voice)`: Cambia voz.
- `set_language(language)`: Cambia idioma.
- `set_rate(rate)`: Velocidad.
- `set_pitch(pitch)`: Tono.
- `set_volume(volume)`: Volumen.
- `register_custom_engine(name, instance)`: Motor custom.
- `enable_cache(enabled)`: Cache.
- `clear_cache()`: Limpia cache.
- `clean_old_files(max_age_seconds)`: Limpia archivos.
- `get_available_engines() -> List[str]`: Motores.
- `get_available_voices() -> Dict`: Voces.
- `get_last_result() -> Dict`: Ultimo resultado.
- `get_info() -> Dict`: Info.
- `speak(text, **kwargs) -> Dict`: Alias de synthesize.

### Enum TTSEngine

Motores: `SYSTEM`, `EDGE`, `PIPER`, `COQUI`, `ELEVENLABS`, `CUSTOM`.

---

## app.audio.audio_analyzer

### class AudioAnalyzer

Analizador de audio en tiempo real.

**Metodos:**

- `initialize()`: Inicializa backend.
- `load(path) -> bool`: Carga WAV.
- `load_stream(samples, sample_rate, channels)`: Carga en memoria.
- `analyze(chunk=None) -> AudioFeatures`: Analiza chunk.
- `reset_position()`: Reinicia lectura.
- `seek(time_seconds)`: Salta a punto.
- `is_finished() -> bool`: Fin de audio.
- `progress() -> float`: Progreso 0.0 a 1.0.
- `set_chunk_size(size)`: Tamano de chunk.
- `set_speech_threshold(rms_threshold)`: Umbral de voz.
- `set_beat_threshold(threshold)`: Umbral de beat.
- `set_smoothing(rms, pitch)`: Suavizado.
- `get_features() -> AudioFeatures`: Features actuales.
- `get_waveform(num_points) -> List[float]`: Forma de onda.
- `get_info() -> Dict`: Info.

---

## app.audio.volume

### class VolumeController

Control de volumen.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, chunk=None)`: Actualiza.
- `apply(chunk) -> Any`: Aplica volumen.
- `fade_to(target, duration, curve)`: Fade.
- `fade_in(duration)` / `fade_out(duration, stop_at)`: Fades.
- `set_master_volume(volume)`: Volumen maestro.
- `set_volume(volume)`: Volumen actual.
- `set_db(db)`: Ajusta por dB.
- `get_db() -> float`: Volumen en dB.
- `mute()` / `unmute()` / `toggle_mute()`: Mute.
- `enable_limiter(enabled, threshold, ratio)`: Limitador.
- `enable_normalization(enabled, target_db, max_gain)`: Normalizacion.
- `set_smoothing(rms, peak_decay)`: Suavizado.
- `get_effective_volume() -> float`: Volumen efectivo.
- `get_level() -> float`: RMS suavizado.
- `get_level_db() -> float`: RMS en dB.
- `get_peak() -> float`: Pico.
- `get_history() -> Dict`: Historial.
- `get_info() -> Dict`: Info.

---

## app.audio.rhythm

### class RhythmController

Deteccion de ritmo y beats.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, features=None)`: Actualiza.
- `is_beat_now(tolerance) -> bool`: Beat previsto.
- `time_to_next_beat() -> float`: Tiempo al siguiente.
- `get_rhythm_intensity() -> float`: Intensidad 0.0 a 1.0.
- `get_beat_punch() -> float`: Punch actual.
- `get_energy_level() -> float`: Energia.
- `set_beat_threshold(threshold)`: Umbral.
- `set_min_interval(seconds)`: Intervalo minimo.
- `set_bpm_range(bpm_min, bpm_max)`: Rango BPM.
- `set_beats_per_bar(beats)`: Beats por compas.
- `enable_prediction(enabled)`: Prediccion.
- `set_smoothing(bpm, energy)`: Suavizado.
- `get_history() -> Dict`: Historial.
- `get_info() -> Dict`: Info.

---

## app.audio.synchronization

### class SynchronizationController

Sincronizacion audio-avatar.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `push_features(timestamp, features)`: Buffer.
- `set_mode(mode)`: Modo.
- `set_latency(latency)`: Latencia.
- `set_weights(lip, head, body)`: Pesos.
- `set_smoothing(value)`: Suavizado.
- `is_synced() -> bool`: Sincronizado.
- `get_signals() -> Dict`: Senales.
- `get_info() -> Dict`: Info.

### Enum SyncMode

Modos: `NONE`, `LIPSYNC`, `FULL`, `EXPRESSIVE`, `PRECISE`.

---

## app.motion.motion_engine

### class MotionEngine

Motor de movimiento.

**Metodos:**

- `initialize()`: Inicializa.
- `register(name, module)`: Submodulo.
- `update(delta, state)`: Actualiza.
- `set_mode(mode)`: Modo.
- `set_intensity(intensity)`: Intensidad.
- `set_weights(head, body, mouth)`: Pesos.
- `trigger_gesture(intensity)`: Dispara gesto.
- `set_idle_params(speed, amplitude)`: Reposo.
- `set_voice_params(scale, smoothing)`: Voz.
- `get_signals() -> Dict`: Senales.
- `get_info() -> Dict`: Info.

### Enum MotionMode

Modos: `DISABLED`, `IDLE`, `VOICE`, `RHYTHM`, `GESTURE`, `COMBINED`, `PRECISE`.

---

## app.motion.smoothing

### class SmoothingController

Suavizado avanzado.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Suaviza estado.
- `smooth_value(key, current, factor, delta) -> float`: Suaviza valor.
- `set_type(s_type)`: Tipo.
- `set_factor(factor)`: Factor global.
- `set_factors(...)`: Factores por componente.
- `set_spring_params(stiffness, damping, mass)`: Muelle.
- `set_velocity_limits(max_velocity, max_acceleration)`: Limites.
- `get_history(key) -> List[float]`: Historial.
- `get_info() -> Dict`: Info.

### Enum SmoothingType

Tipos: `LERP`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`, `EXPONENTIAL`, `SPRING`, `CRITICAL_DAMP`.

---

## app.motion.idle_motion

### class IdleMotionController

Movimiento en reposo.

**Metodos:**

- `initialize()`: Inicializa.
- `register(name, module)`: Submodulo.
- `update(delta, state)`: Actualiza.
- `set_mode(mode)`: Modo.
- `set_intensity(intensity)`: Intensidad.
- `set_look_interval(min_s, max_s)`: Intervalo de mirada.
- `set_look_amplitude(amplitude)`: Amplitud.
- `enable(enabled)`: Activa.
- `suspend()` / `resume()`: Suspende.
- `get_info() -> Dict`: Info.

### Enum IdleMode

Modos: `CALM`, `CURIOUS`, `SLEEPY`, `ENERGETIC`, `FOCUSED`, `BREATHING`.

---

## app.motion.voice_motion

### class VoiceMotionController

Movimiento reactivo a voz.

**Metodos:**

- `initialize()`: Inicializa.
- `register(name, module)`: Submodulo.
- `update(delta, state)`: Actualiza.
- `set_mode(mode)`: Modo.
- `set_intensity(intensity)`: Intensidad.
- `set_head_speed(speed)` / `set_body_speed(speed)`: Velocidades.
- `set_attack_release(attack, release)`: Ataque/liberacion.
- `set_smoothing(rms, pitch, energy, beat)`: Suavizado.
- `enable(enabled)`: Activa.
- `suspend()` / `resume()`: Suspende.
- `get_signals() -> Dict`: Senales.
- `get_info() -> Dict`: Info.

### Enum VoiceMotionMode

Modos: `SUBTLE`, `NATURAL`, `EXPRESSIVE`, `DRAMATIC`, `MINIMAL`.

---

## app.gestures.neutral

### class NeutralGesture

Gesto neutral.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `activate()` / `deactivate()`: Activa.
- `set_variant(variant)`: Variante.
- `set_intensity(intensity)`: Intensidad.
- `set_smoothing(factor)`: Suavizado.
- `set_transition_speed(speed)`: Transicion.
- `override_pose(...)`: Sobrescribe pose.
- `get_type() -> GestureType`: Tipo.
- `is_active() -> bool`: Activo.
- `get_pose() -> Dict`: Pose.
- `get_info() -> Dict`: Info.

### Enum NeutralVariant

Variantes: `BASE`, `ATTENTIVE`, `RELAXED`, `FRIENDLY`, `PROFESSIONAL`, `CONTEMPLATIVE`.

---

## app.gestures.question

### class QuestionGesture

Gesto de pregunta.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `activate(hold_duration)`: Activa.
- `deactivate()`: Desactiva.
- `set_variant(variant)`: Variante.
- `set_hold_duration(duration)`: Mantenimiento.
- `set_intensity(intensity)`: Intensidad.
- `set_smoothing(factor)`: Suavizado.
- `set_transition_speed(speed)`: Transicion.
- `set_auto_exit(auto)`: Salida automatica.
- `on_finish(callback)`: Callback.
- `get_type() -> GestureType`: Tipo.
- `is_active() -> bool`: Activo.
- `get_phase() -> str`: Fase.
- `get_pose() -> Dict`: Pose.
- `get_info() -> Dict`: Info.

### Enum QuestionVariant

Variantes: `NEUTRAL`, `CURIOUS`, `SURPRISED`, `CONFUSED`, `INTRIGUED`, `SKEPTICAL`.

---

## app.gestures.talking

### class TalkingGesture

Gesto de habla.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `activate()` / `deactivate()`: Activa/desactiva.
- `set_variant(variant)`: Variante.
- `set_intensity(intensity)`: Intensidad.
- `set_auto_exit(enabled, silence_timeout, silence_threshold)`: Salida.
- `set_nod_chance(chance)`: Nodding.
- `set_smoothing(...)`: Suavizado.
- `on_finish(callback)`: Callback.
- `get_type() -> GestureType`: Tipo.
- `is_active() -> bool`: Activo.
- `get_signals() -> Dict`: Senales.
- `get_info() -> Dict`: Info.

### Enum TalkingVariant

Variantes: `NORMAL`, `ENTHUSIASTIC`, `CALM`, `EXCITED`, `SERIOUS`, `FRIENDLY`.

---

## app.interface.controls

### class ControlsController

Control de acciones.

**Metodos:**

- `attach_engine(engine)`: Vincula motor.
- `register_callback(action, callback)`: Callback.
- `execute(action, **kwargs) -> Dict`: Ejecuta accion.
- `lock(reason)` / `unlock()`: Bloqueo.
- `get_history() -> List[Dict]`: Historial.
- `get_last_action() -> Dict`: Ultima accion.
- `get_info() -> Dict`: Info.
- `get_available_actions() -> List[str]`: Acciones.

### Enum ControlAction

Acciones: `PLAY`, `PAUSE`, `STOP`, `RESTART`, `SPEAK`, `SET_GESTURE`, `START_RECORDING`, `STOP_RECORDING`, `EXPORT_VIDEO`, `MUTE`, `UNMUTE`, `SET_VOLUME`, `LOAD_AVATAR`, `UNLOAD_AVATAR`, `SET_MODE`.

---

## app.interface.settings

### class SettingsController

Configuracion persistente.

**Metodos:**

- `load(path=None) -> bool`: Carga.
- `save(path=None) -> bool`: Guarda.
- `reset(section=None)`: Reinicia.
- `get(path, default) -> Any`: Obtiene valor.
- `set(path, value) -> bool`: Establece valor.
- `update(updates)`: Multiples cambios.
- `delete(path) -> bool`: Elimina clave.
- `apply_profile(profile)`: Aplica perfil.
- `get_current_profile() -> SettingsProfile`: Perfil activo.
- `apply_to_engine(engine)`: Aplica al motor.
- `update(delta)`: Autosave.
- `enable_autosave(enabled, interval)`: Autosave.
- `export_to(path) -> bool` / `import_from(path) -> bool`: Import/export.
- `get_all() -> Dict` / `get_section(name) -> Dict`: Acceso.
- `get_history() -> List[Dict]`: Historial.
- `get_info() -> Dict`: Info.

### Enum SettingsProfile

Perfiles: `DEFAULT`, `PERFORMANCE`, `QUALITY`, `LOW_END`, `STREAMING`, `DEBUG`.

---

## app.interface.preview

### class PreviewController

Vista previa.

**Metodos:**

- `initialize()`: Inicializa.
- `update(delta, state)`: Actualiza.
- `add_overlay(overlay)` / `remove_overlay(overlay)` / `toggle_overlay(overlay)`: Overlays.
- `clear_overlays()` / `set_overlays(overlays)`: Set completo.
- `set_mode(mode)` / `cycle_mode()`: Modos.
- `set_resolution(width, height)`: Resolucion.
- `set_scale(scale)` / `set_offset(x, y)` / `reset_view()`: Vista.
- `set_background(color)` / `set_grid(enabled, size, color)`: Apariencia.
- `show()` / `hide()` / `toggle_visibility()`: Visibilidad.
- `enable(enabled)` / `pause()` / `resume()`: Control.
- `get_last_snapshot() -> Dict`: Snapshot.
- `set_snapshot_interval(interval)`: Intervalo.
- `get_overlay_data() -> Dict`: Datos.
- `get_info() -> Dict`: Info.

### Enum PreviewMode

Modos: `NORMAL`, `WIREFRAME`, `DEBUG`, `GRID`, `OVERLAY`, `COMPACT`.

### Enum OverlayType

Overlays: `FPS`, `FRAME`, `STATE`, `SIGNALS`, `BOUNDS`, `GRID`, `TIMER`, `RECORDING`.

---

## app.output.recorder

### class Recorder

Grabador de frames.

**Metodos:**

- `initialize()`: Inicializa backends.
- `set_backend(backend)`: Backend.
- `start(output_path, fps, resolution, audio_path) -> bool`: Inicia.
- `capture_frame(frame=None)`: Captura.
- `pause()` / `resume()`: Pausa.
- `stop() -> float`: Detiene.
- `finalize() -> float`: Alias.
- `attach_audio(audio_path)` / `detach_audio()`: Audio.
- `set_limits(max_frames, max_duration)`: Limites.
- `set_codec(codec)`: Codec.
- `is_recording() -> bool` / `is_paused() -> bool`: Estado.
- `duration() -> float`: Duracion.
- `get_info() -> Dict`: Info.

### Enum RecorderBackend

Backends: `OPENCV`, `IMAGEIO`, `FFMPEG`, `RAW`.

---

## app.output.video_export

### class VideoExporter

Exportador de video.

**Metodos:**

- `initialize()`: Detecta backends.
- `set_ffmpeg_path(path)`: Ruta ffmpeg.
- `export(input_path, output_path, format, quality, audio_path) -> bool`: Exporta.
- `convert(input_path, format, output_path, quality) -> bool`: Convierte.
- `extract_audio(input_path, output_path) -> bool`: Extrae audio.
- `generate_thumbnail(input_path, output_path, timestamp) -> bool`: Miniatura.
- `set_format(fmt)` / `set_quality(quality)` / `set_fps(fps)`: Configuracion.
- `set_resolution(width, height)`: Resolucion.
- `set_audio(enabled, audio_path)`: Audio.
- `set_metadata(key, value)` / `clear_metadata()`: Metadata.
- `get_info() -> Dict`: Info.
- `get_available_formats() -> List[str]`: Formatos.
- `get_available_qualities() -> List[str]`: Calidades.

### Enum ExportFormat

Formatos: `MP4`, `WEBM`, `MKV`, `MOV`, `GIF`.

### Enum ExportQuality

Calidades: `LOW`, `MEDIUM`, `HIGH`, `ULTRA`, `LOSSLESS`.
XARION_EOF
echo "[OK] docs/api.md"