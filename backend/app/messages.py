from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import yaml


@dataclass
class UserMessage:
    message: str

    def as_std_message_format(self) -> Dict[str, str]:
        return {
            "role": "user",
            "content": self.message,
        }

    def as_message_dict(self) -> Dict[str, str]:
        return {
            "role": "user",
            "content": self.message,
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

    def as_std_message_format(self) -> Dict[str, str]:
        return {
            "role": "user",
            "content": yaml.dump(
                {
                    "personality_state": self.personality_state,
                    "emotions": [list(emotion_tuple) for emotion_tuple in self.emotions],
                    "thoughts": self.thoughts,
                    "reaction_emoji": self.reaction_emoji,
                    "messages": self.messages,
                },
                sort_keys=False,
            ),
        }

    def as_message_dict(self) -> Dict[str, Union[str, Dict]]:
        return {
            "role": "user",
            "content": {
                "personality_state": self.personality_state,
                "emotions": [list(emotion_tuple) for emotion_tuple in self.emotions],
                "thoughts": self.thoughts,
                "reaction_emoji": self.reaction_emoji,
                "messages": self.messages,
            },
        }

    def __repr__(self) -> str:
        return yaml.dump(
            self.as_message_dict(),
            sort_keys=False,
        )
