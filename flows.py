from typing import Annotated, Any, Dict, List, Tuple, Union

from pocketflow import Flow, Node
from pydantic import BaseModel, conint
from typing_extensions import TypedDict

import memory
import messages
import prompts
from llm import call_llm, extract_yaml

# *TODO: summariser every convo end, outer loop every 5-10 turns (config?), inner loop every turn


class InnerLoopStepResult(BaseModel):
    personality_state: str
    emotions: List[Tuple[str, Annotated[int, conint(ge=1, le=10)]]]
    thoughts: List[str]
    message: str


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
                    "content": prompts.INNER_LOOP_AGENT_PROMPT.format(memory=memory),
                }
            ]
            + [message.as_std_message_format() for message in conversation_history]
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
        shared["conversation_history"].append(
            messages.AgentMessage(
                personality_state=exec_res.personality_state,
                emotions=exec_res.emotions,
                thoughts=exec_res.thoughts,
                message=exec_res.message,
            )
        )
        shared["response"] = exec_res.message


inner_loop_step_node = InnerLoopStep(max_retries=10)


class NewMutablePersonalityTraitsDict(TypedDict):
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


class OuterLoopResult(BaseModel):
    analysis: str
    new_mutable_personality_traits: NewMutablePersonalityTraitsDict
    new_auxiliary_memory: NewAuxiliaryMemoryDict


class OuterLoopStep(Node):
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
                    "content": prompts.INNER_LOOP_AGENT_PROMPT.format(memory=memory),
                }
            ]
            + [message.as_std_message_format() for message in conversation_history]
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
        shared["conversation_history"].append(
            messages.AgentMessage(
                personality_state=exec_res.personality_state,
                emotions=exec_res.emotions,
                thoughts=exec_res.thoughts,
                message=exec_res.message,
            )
        )
        shared["response"] = exec_res.message


outer_loop_step_node = OuterLoopStep(max_retries=10)


if __name__ == "__main__":
    print("THIS IS A TEST FOR flows.py (inner loop)")

    assert input("DO YOU WISH TO PROCEED? (y/n) ").strip() == "y", "abort"

    shared = {
        "memory": memory.DEFAULT_MEMORY,
        "conversation_history": [
            messages.UserMessage(
                message="(SYSTEM) User has entered the conversation for the first time"
            )
        ],
    }
    inner_loop_step_node.run(shared)
    print(f"Agent Message: {shared['response']}")
    print(f"Full Agent Response:\n{shared['conversation_history'][-1]}")
