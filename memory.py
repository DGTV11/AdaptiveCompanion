from dataclasses import dataclass
from typing import NamedTuple, Optional, Tuple


class MutablePersonalityTrait(NamedTuple):
    previous_value: Optional[int]
    current_value: int


@dataclass
class CorePersonality:
    name: str
    likes: str
    dislikes: str
    mode_of_communication: str


@dataclass
class MutablePersonality:
    humanlikeness: MutablePersonalityTrait
    affection: MutablePersonalityTrait
    warmth: MutablePersonalityTrait
    enthusiasm: MutablePersonalityTrait
    impulsiveness: MutablePersonalityTrait
    curiosity: MutablePersonalityTrait
    quirkiness: MutablePersonalityTrait
    shyness: MutablePersonalityTrait
    nerdiness: MutablePersonalityTrait
    cuteness: MutablePersonalityTrait


@dataclass
class AuxilliaryMemory:
    user_memory: str
    memory_scratchpad: str
    interaction_summary: str


@dataclass
class Memory:
    core_personality: CorePersonality
    mutable_personality: MutablePersonality
    auxilliary_memory: AuxilliaryMemory
