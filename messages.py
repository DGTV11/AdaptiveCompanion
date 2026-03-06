from dataclasses import dataclass
from typing import Dict, List, Tuple

import yaml


@dataclass
class UserMessage:
    message: str

    def as_std_message_format(self) -> Dict[str, str]:
        return {
            "role": "user",
            "content": self.message,
        }

    def __repr__(self) -> str:
        return yaml.dump(self.as_std_message_format(), sort_keys=False)


@dataclass
class AgentMessage:
    personality_state: str
    emotions: List[Tuple[str, int]]
    thoughts: List[str]
    message: str

    def as_std_message_format(self) -> Dict[str, str]:
        return {
            "role": "user",
            "content": yaml.dump(
                {
                    "personality_state": self.personality_state,
                    "emotions": self.emotions,
                    "thoughts": self.thoughts,
                    "message": self.message,
                },
                sort_keys=False,
            ),
        }

    def __repr__(self) -> str:
        return yaml.dump(
            {
                "role": "user",
                "content": {
                    "personality_state": self.personality_state,
                    "emotions": self.emotions,
                    "thoughts": self.thoughts,
                    "message": self.message,
                },
            },
            sort_keys=False,
        )
