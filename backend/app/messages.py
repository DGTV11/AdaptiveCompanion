from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


@dataclass
class UserMessage:
    message: str
    reaction_emoji: Optional[str]
    timestamp: datetime

    def as_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "reaction_emoji": self.reaction_emoji,
            "timestamp": self.timestamp,
        }

    def as_std_message_format(self) -> Dict[str, str]:
        return {
            "role": "user",
            "content": yaml.dump(
                self.as_dict(),
                sort_keys=False,
            ),
        }

    def as_message_dict(self) -> Dict[str, Union[str, Dict]]:
        return {
            "role": "user",
            "content": self.as_dict(),
        }

    def __repr__(self) -> str:
        return yaml.dump(self.as_message_dict(), sort_keys=False)


@dataclass
class AgentMessage:
    personality_state: str
    emotions: List[Tuple[str, int]]
    thoughts: List[str]
    reaction_emoji: Optional[str]
    messages: Optional[List[str]]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "personality_state": self.personality_state,
            "emotions": [list(emotion_tuple) for emotion_tuple in self.emotions],
            "thoughts": self.thoughts,
            "reaction_emoji": self.reaction_emoji,
            "messages": self.messages,
        }

    def as_std_message_format(self) -> Dict[str, str]:
        return {
            "role": "assistant",
            "content": yaml.dump(
                self.as_dict(),
                sort_keys=False,
            ),
        }

    def as_message_dict(self) -> Dict[str, Union[str, Dict]]:
        return {
            "role": "assistant",
            "content": self.as_dict(),
        }

    def __repr__(self) -> str:
        return yaml.dump(
            self.as_message_dict(),
            sort_keys=False,
        )
