# app/gestures/__init__.py

"""
Modulo de gestos de XARION 1.0.

Expone los gestos programados del avatar:

- NeutralGesture        -> gesto base con variantes de pose
- NeutralVariant        -> variantes (base, attentive, relaxed, friendly...)
- NEUTRAL_VARIANTS      -> perfiles por variante
- QuestionGesture       -> gesto de pregunta con fases enter/hold/exit
- QuestionVariant       -> variantes (neutral, curious, surprised, confused...)
- QUESTION_VARIANTS     -> perfiles por variante
- TalkingGesture        -> gesto de habla reactivo a audio
- TalkingVariant        -> variantes (normal, enthusiastic, calm...)
- TALKING_VARIANTS      -> perfiles por variante
"""

from app.gestures.neutral import (
    NeutralGesture,
    NeutralVariant,
    NEUTRAL_VARIANTS,
)
from app.gestures.question import (
    QuestionGesture,
    QuestionVariant,
    QUESTION_VARIANTS,
)
from app.gestures.talking import (
    TalkingGesture,
    TalkingVariant,
    TALKING_VARIANTS,
)

__all__ = [
    "NeutralGesture",
    "NeutralVariant",
    "NEUTRAL_VARIANTS",
    "QuestionGesture",
    "QuestionVariant",
    "QUESTION_VARIANTS",
    "TalkingGesture",
    "TalkingVariant",
    "TALKING_VARIANTS",
]