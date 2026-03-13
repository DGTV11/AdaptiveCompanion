from dataclasses import fields
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, Tuple, Union, cast

import memory
import messages
import prompts
import yaml
from emoji import is_emoji
from llm import call_llm, extract_yaml
from pocketflow import Flow, Node
from pydantic import BaseModel, conint, validator
from typing_extensions import TypedDict


class InnerLoopStepResult(BaseModel):
    personality_state: str
    emotions: List[Tuple[str, Annotated[int, conint(ge=1, le=10)]]]
    thoughts: List[str]
    reaction_emoji: Optional[str]
    messages: Optional[List[str]]

    @validator("reaction_emoji")
    def must_be_single_emoji(cls, v):
        if v is None:
            return v
        if not is_emoji(v):
            raise ValueError("reaction_emoji must be a single emoji character")
        return v


class InnerLoopStep(Node):
    def prep(
        self, shared: Dict[str, Any]
    ) -> Tuple[memory.Memory, List[Union[messages.UserMessage, messages.AgentMessage]]]:
        memory = shared["memory"]
        conversation_history = shared["conversation_history"]
        return memory, conversation_history

    def exec(
        self,
        prep_res: Tuple[
            memory.Memory, List[Union[messages.UserMessage, messages.AgentMessage]]
        ],
    ) -> InnerLoopStepResult:
        memory, conversation_history = prep_res

        resp = call_llm(
            [
                {
                    "role": "system",
                    "content": prompts.INNER_LOOP_AGENT_PROMPT.format(
                        memory=memory,
                    ),
                }
            ]
            + [turn.as_std_message_format() for turn in conversation_history]
        )

        result = extract_yaml(resp)
        result_validated = InnerLoopStepResult.model_validate(result)

        return result_validated

    def post(
        self,
        shared: Dict[str, Any],
        prep_res: Tuple[
            memory.Memory, List[Union[messages.UserMessage, messages.AgentMessage]]
        ],
        exec_res: InnerLoopStepResult,
    ):
        shared["last_response"] = messages.AgentMessage(
            personality_state=exec_res.personality_state,
            emotions=exec_res.emotions,
            thoughts=exec_res.thoughts,
            reaction_emoji=exec_res.reaction_emoji,
            messages=exec_res.messages,
        )
        shared["conversation_history"].append(shared["last_response"])
        shared["reaction_emoji"] = exec_res.reaction_emoji
        shared["messages"] = exec_res.messages


inner_loop_step_node = InnerLoopStep(max_retries=10)


class NewMutablePersonalityDict(TypedDict):
    humanlikeness: Annotated[int, conint(ge=0, le=10)]
    affection: Annotated[int, conint(ge=0, le=10)]
    warmth: Annotated[int, conint(ge=0, le=10)]
    enthusiasm: Annotated[int, conint(ge=0, le=10)]
    impulsiveness: Annotated[int, conint(ge=0, le=10)]
    curiosity: Annotated[int, conint(ge=0, le=10)]
    quirkiness: Annotated[int, conint(ge=0, le=10)]
    shyness: Annotated[int, conint(ge=0, le=10)]
    nerdiness: Annotated[int, conint(ge=0, le=10)]
    cuteness: Annotated[int, conint(ge=0, le=10)]


class NewAuxiliaryMemoryDict(TypedDict):
    user_memory: str
    scratchpad: str


class OuterLoopOptimiserStepResult(BaseModel):
    analysis: str
    mutable_personality_optimisation_planning: str
    new_mutable_personality: NewMutablePersonalityDict
    auxiliary_memory_update_planning: str
    new_auxiliary_memory: NewAuxiliaryMemoryDict


class OuterLoopOptimiserStep(Node):
    def prep(
        self, shared: Dict[str, Any]
    ) -> Tuple[memory.Memory, List[Union[messages.UserMessage, messages.AgentMessage]]]:
        memory = shared["memory"]
        conversation_history = shared["conversation_history"]
        return memory, conversation_history

    def exec(
        self,
        prep_res: Tuple[
            memory.Memory, List[Union[messages.UserMessage, messages.AgentMessage]]
        ],
    ) -> OuterLoopOptimiserStepResult:
        memory, conversation_history = prep_res

        resp = call_llm(
            [
                {
                    "role": "system",
                    "content": prompts.OUTER_LOOP_OPTIMISER_PROMPT.format(
                        memory=memory,
                    ),
                },
                {
                    "role": "user",
                    "content": yaml.dump(
                        [turn.as_message_dict() for turn in conversation_history],
                        sort_keys=False,
                    ),
                },
            ]
        )

        result = extract_yaml(resp)
        result_validated = OuterLoopOptimiserStepResult.model_validate(result)

        return result_validated

    def post(
        self,
        shared: Dict[str, Any],
        prep_res: Tuple[
            memory.Memory, List[Union[messages.UserMessage, messages.AgentMessage]]
        ],
        exec_res: OuterLoopOptimiserStepResult,
    ):
        memory, conversation_history = prep_res

        # *Update Mutable Personality
        new_mutable_personality = cast(dict[str, Any], exec_res.new_mutable_personality)
        mutable_personality = memory.mutable_personality

        for trait_field in fields(mutable_personality):
            trait_name = trait_field.name
            # print(trait_name)
            assert trait_name in new_mutable_personality.keys()
            mutable_personality_trait = getattr(mutable_personality, trait_name)
            mutable_personality_trait.previous_value = (
                mutable_personality_trait.current_value
            )
            mutable_personality_trait.current_value = new_mutable_personality[
                trait_name
            ]

        # *Update Auxiliary Memory
        auxiliary_memory = memory.auxiliary_memory
        new_auxiliary_memory = exec_res.new_auxiliary_memory

        auxiliary_memory.user_memory = new_auxiliary_memory["user_memory"]
        auxiliary_memory.scratchpad = new_auxiliary_memory["scratchpad"]


outer_loop_optimiser_step_node = OuterLoopOptimiserStep(max_retries=10)


class OuterLoopSummariserStepResult(BaseModel):
    analysis: str
    new_interaction_summary: str


class OuterLoopSummariserStep(Node):
    def prep(
        self, shared: Dict[str, Any]
    ) -> Tuple[memory.Memory, List[Union[messages.UserMessage, messages.AgentMessage]]]:
        memory = shared["memory"]
        conversation_history = shared["conversation_history"]
        return memory, conversation_history

    def exec(
        self,
        prep_res: Tuple[
            memory.Memory, List[Union[messages.UserMessage, messages.AgentMessage]]
        ],
    ) -> OuterLoopSummariserStepResult:
        memory, conversation_history = prep_res

        resp = call_llm(
            [
                {
                    "role": "system",
                    "content": prompts.OUTER_LOOP_SUMMARISER_PROMPT.format(
                        memory=memory,
                    ),
                },
                {
                    "role": "user",
                    "content": yaml.dump(
                        [turn.as_message_dict() for turn in conversation_history],
                        sort_keys=False,
                    ),
                },
            ]
        )

        result = extract_yaml(resp)
        result_validated = OuterLoopSummariserStepResult.model_validate(result)

        return result_validated

    def post(
        self,
        shared: Dict[str, Any],
        prep_res: Tuple[
            memory.Memory, List[Union[messages.UserMessage, messages.AgentMessage]]
        ],
        exec_res: OuterLoopSummariserStepResult,
    ):
        memory, conversation_history = prep_res

        # *Update Interaction Summary
        auxiliary_memory = memory.auxiliary_memory
        new_interaction_summary = exec_res.new_interaction_summary

        auxiliary_memory.interaction_summary = new_interaction_summary


outer_loop_summariser_step_node = OuterLoopSummariserStep(max_retries=10)


if __name__ == "__main__":
    print("THIS IS A TEST FOR flows.py (inner loop)")

    assert input("DO YOU WISH TO PROCEED? (y/n) ").strip() == "y", "abort"

    shared = {
        "memory": memory.DEFAULT_MEMORY,
        "conversation_history": [
            messages.UserMessage(
                message="(SYSTEM) User has entered the conversation for the first time. Suggestion: introduce yourself/get to know the user.",
                timestamp=datetime.now(),
            )
        ],
    }
    inner_loop_step_node.run(shared)
    print(f"Agent Messages: {shared['messages']}")
    print(f"Full Agent Response:\n{shared['last_response']}")
