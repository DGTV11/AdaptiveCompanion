from asyncio import Queue
from collections.abc import AsyncIterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict, Union
from uuid import UUID, uuid4

import config
import db
import flows
import jwt
import memory
import messages
from emoji import is_emoji
from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, status
from fastapi.responses import ORJSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.sse import EventSourceResponse
from humanize import precisedelta
from jwt.exceptions import InvalidTokenError
from password_strength import PasswordPolicy
from pwdlib import PasswordHash
from pydantic import BaseModel, Field, RootModel, field_validator, validator

# def interact_with_agent(
#     agent_id: UUID, last_user_message_time: Optional[datetime], agent_name: str
# ):
#     print("Generating first agent message...", flush=True)
#     shared = {
#         "memory": memory.Memory.read_from_db(agent_id),
#         "conversation_history": [],
#     }
#
#     first_message = (
#         "(SYSTEM) User has entered the conversation for the first time. Suggestion: introduce yourself/get to know the user."
#         if not last_user_message_time
#         else f"(SYSTEM) User has reentered the conversation (last user message {precisedelta(datetime.now() - last_user_message_time, minimum_unit='minutes')} ago)."
#     )
#     print(first_message, flush=True)
#
#     run_inner_loop(
#         shared,
#         agent_id,
#         first_message,
#     )
#     if shared["messages"]:
#         for message in shared["messages"]:
#             print(f"{agent_name}: {message}", end="\n\n", flush=True)
#
#     user_message = ""
#     user_message_count = 0
#     try:
#         while user_message != "quit":
#             print(
#                 'You (enter "/quit" or "/exit" to quit, "/help" for help): ',
#                 end="",
#                 flush=True,
#             )
#             user_message = input().strip()
#             print(flush=True)
#
#             match user_message:
#                 case "":
#                     continue
#                 case "/quit":
#                     break
#                 case "/exit":
#                     break
#                 case "/help":
#                     print(
#                         """
#     /help - display this help message
#     /quit - quit
#     /exit - exit
#     /memory - display agent memory view
#     /last-response - display last agent full response
#                     """,
#                         end="\n\n",
#                         flush=True,
#                     )
#                     continue
#                 case "/memory":
#                     print(repr(shared["memory"]), end="\n\n", flush=True)
#                     continue
#                 case "/last-response":
#                     if len(shared["conversation_history"]) == 0:
#                         print("No last agent full response", flush=True)
#                     else:
#                         print(shared["last_response"], flush=True)
#                     continue
#                 case _:
#                     user_message = f"(USER) {user_message}"
#                     if (
#                         user_message_count > 0
#                         and user_message_count
#                         % config.OPTIMISER_FREQUENCY_IN_USER_MESSAGES
#                         == 0
#                     ):
#                         user_message = f"(SYSTEM) Personality optimisations and auxiliary memory updates complete. Interaction summary has been updated and older messages have been truncated.\n\n{user_message}"
#
#                     run_inner_loop(
#                         shared,
#                         agent_id,
#                         user_message,
#                     )
#                     if shared["reaction_emoji"]:
#                         print(
#                             f"{agent_name} reacted {shared["reaction_emoji"]} to your message",
#                             flush=True,
#                         )
#
#                     if shared["messages"]:
#                         for message in shared["messages"]:
#                             print(f"{agent_name}: {message}", end="\n\n", flush=True)
#
#             user_message_count += 1
#             if user_message_count % config.OPTIMISER_FREQUENCY_IN_USER_MESSAGES == 0:
#                 last_3_user_agent_turns = shared["conversation_history"][-(3 * 2) :]
#                 shared["conversation_history"] = shared["conversation_history"][
#                     : -(3 * 2)
#                 ]
#
#                 run_outer_loop(shared, agent_id)
#
#                 shared["conversation_history"] = last_3_user_agent_turns
#
#                 print(
#                     "(SYSTEM) Personality optimisations and auxiliary memory updates complete. Interaction summary has been updated and older messages have been truncated.",
#                     flush=True,
#                 )
#     except KeyboardInterrupt:
#         pass
#
#     print("Exiting...", flush=True)
#
#     run_outer_loop(shared, agent_id)
#
#     print(
#         "(SYSTEM) Personality optimisations and auxiliary memory updates complete.",
#         flush=True,
#     )


# *Models/Dataclasses


# **Auth

password_policy = policy = PasswordPolicy.from_names(
    length=8,
    uppercase=1,
    numbers=1,
    special=1,
    nonletters=1,
)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    id: UUID
    created_at: datetime
    username: str


class UserInDB(User):
    hashed_password: str


class UserCreateFormData(BaseModel):
    username: str
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("confirm_password")
    def password_is_strong(cls, v, info):
        password_strength_errors = password_policy.test(v)
        if len(password_strength_errors) > 0:
            unmet_requirements = ", ".join(
                [
                    f"{type(error).__name__} >= {error.args[0]}"
                    for error in password_strength_errors
                ]
            )

            raise ValueError(
                f"Password not strong enough (unmet requirements: {unmet_requirements})"
            )
        return v


# **Agents


class AgentInfo(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    last_user_message_time: datetime


class CorePersonalityDict(TypedDict):
    name: str
    likes: str
    dislikes: str
    desires: str
    mode_of_communication: str


class MutablePersonalityDict(TypedDict):
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


class CustomPersonalityFormData(BaseModel):
    core_personality: CorePersonalityDict
    mutable_personality: MutablePersonalityDict


# **Events


class AgentMessageEvent(BaseModel):
    event_type: Literal["agent"] = "agent"
    message: messages.AgentMessage


class SystemEvent(BaseModel):
    event_type: Literal["system"] = "system"
    message: str


class ExitEvent(BaseModel):
    event_type: Literal["exit"] = "exit"


class Event(RootModel):
    root: Union[AgentMessageEvent, SystemEvent, ExitEvent] = Field(
        discriminator="event_type"
    )


# **Sessions


class SessionInfo(BaseModel):
    agent_id: UUID
    agent_name: str


@dataclass
class SessionRuntime:
    agent_id: UUID
    agent_name: str
    user_message_count: int
    shared: Dict[str, Any]
    event_queue: Queue[Event]


sessions_by_user: Dict[UUID, Dict[UUID, SessionRuntime]] = dict()


# **Message sending
class UserMessageFormData(BaseModel):
    reaction_emoji: Optional[str]
    message: str

    @validator("reaction_emoji")
    def must_be_single_emoji(cls, v):
        if v is None:
            return v
        if not is_emoji(v):
            raise ValueError("reaction_emoji must be a single emoji character")
        return v


# *API

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(default_response_class=ORJSONResponse)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def get_user(username: str):
    matched_users = db.read(
        "SELECT * FROM users WHERE username = %s",
        (username,),
    )

    if matched_users:
        id, created_at, username, hashed_password = matched_users[0]
        return UserInDB(
            id=id,
            created_at=created_at,
            username=username,
            hashed_password=hashed_password,
        )


def authenticate_user(username: str, password: str):
    user = get_user(username)

    if not user:
        verify_password(password, DUMMY_HASH)  # *prevent timing attacks
        return False
    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
        if token_data.username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post("/users")
async def new_user(form_data: Annotated[UserCreateFormData, Form()]):
    username_exists = bool(
        len(
            db.read(
                "SELECT users.id FROM users WHERE users.username = %s",
                (form_data.username,),
            )
        )
    )

    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if (
        db.read(
            "SELECT COUNT(*) FROM users",
        )[
            0
        ][0]
        >= config.MAX_USERS
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User limit reached",
            headers={"WWW-Authenticate": "Bearer"},
        )  # TODO: future me problem: fix potential race condition using locking

    hashed_password = get_password_hash(form_data.password)

    db.write(
        "INSERT INTO users (username, hashed_password) VALUES (%s, %s)",
        (form_data.username, hashed_password),
    )


@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@app.delete("/users/me")
async def delete_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    db.write(
        "DELETE FROM users WHERE id = %s",
        (current_user.id,),
    )


@app.get("/agents")
async def list_agents(
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[AgentInfo]:
    return [
        AgentInfo(**{k: v for k, v in zip(AgentInfo.model_fields.keys(), agent_info)})
        for agent_info in db.read(
            """
SELECT agents.id, core_personality.name, agents.created_at, agents.last_user_message_time FROM agents WHERE agents.user_id = %s
INNER JOIN core_personality ON agents.id = core_personality.agent_id
    """,
            (current_user.id,),
        )
    ]


@app.get("/agent/{agent_id}")
async def get_agent(
    agent_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    agent_exists = bool(
        len(
            db.read(
                "SELECT agents.id FROM agents WHERE agents.user_id = %s AND agents.id = %s",
                (current_user.id, agent_id),
            )
        )
    )

    if agent_exists:
        return memory.Memory.read_from_db(agent_id).as_dict()

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Agent not found",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.delete("/agent/{agent_id}")
async def delete_agent(
    agent_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    agent_exists = bool(
        len(
            db.read(
                "SELECT agents.id FROM agents WHERE agents.user_id = %s AND agents.id = %s",
                (current_user.id, agent_id),
            )
        )
    )

    if agent_exists:
        db.write(
            "DELETE FROM agents WHERE agents.user_id = %s AND agents.id = %s",
            (current_user.id, agent_id),
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Agent not found",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.post("/agents/default", status_code=201)
async def create_agent_with_default_personality(
    current_user: Annotated[User, Depends(get_current_user)],
):
    agent_id = uuid4()

    memory_data = memory.DEFAULT_MEMORY

    db.write(
        "INSERT INTO agents (id, user_id) VALUES (%s, %s)", (agent_id, current_user.id)
    )
    memory_data.insert_into_db(agent_id)


@app.post("/agents/custom")
async def create_agent_with_custom_personality(
    form_data: Annotated[CustomPersonalityFormData, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
):
    agent_id = uuid4()

    memory_data = memory.Memory(
        core_personality=memory.CorePersonality(
            name=form_data.core_personality["name"],
            likes=form_data.core_personality["likes"],
            dislikes=form_data.core_personality["dislikes"],
            desires=form_data.core_personality["desires"],
            mode_of_communication=form_data.core_personality["mode_of_communication"],
        ),
        mutable_personality=memory.MutablePersonality(
            humanlikeness=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["humanlikeness"],
            ),
            affection=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["affection"],
            ),
            warmth=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["warmth"],
            ),
            enthusiasm=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["enthusiasm"],
            ),
            impulsiveness=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["impulsiveness"],
            ),
            curiosity=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["curiosity"],
            ),
            quirkiness=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["quirkiness"],
            ),
            shyness=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["shyness"],
            ),
            nerdiness=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["nerdiness"],
            ),
            cuteness=memory.MutablePersonalityTrait(
                previous_value=None,
                current_value=form_data.mutable_personality["cuteness"],
            ),
        ),
        auxiliary_memory=memory.AuxiliaryMemory(
            user_memory="Nothing yet",
            scratchpad="Nothing yet",
            interaction_summary="Nothing yet",
        ),
    )
    db.write(
        "INSERT INTO agents (id, user_id) VALUES (%s, %s)", (agent_id, current_user.id)
    )
    memory_data.insert_into_db(agent_id)


@app.get("/sessions")
async def list_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[SessionInfo]:
    return [
        SessionInfo(agent_id=session.agent_id, agent_name=session.agent_name)
        for session in sessions_by_user[current_user.id].values()
    ]


def run_outer_loop(runtime: SessionRuntime, agent_id: UUID):
    flows.outer_loop_optimiser_step_node.run(runtime.shared)
    flows.outer_loop_summariser_step_node.run(runtime.shared)

    runtime.shared["memory"].update_db(agent_id)


async def run_inner_loop(
    runtime: SessionRuntime,
    agent_id: UUID,
    user_message: str,
    reaction_emoji: Optional[str],
):
    user_message = f"(USER) {user_message}"
    if (
        runtime.user_message_count > 0
        and runtime.user_message_count % config.OPTIMISER_FREQUENCY_IN_USER_MESSAGES
        == 0
    ):
        user_message = f"(SYSTEM) Personality optimisations and auxiliary memory updates complete. Interaction summary has been updated and older messages have been truncated.\n\n{user_message}"

    runtime.shared["conversation_history"].append(
        messages.UserMessage(
            timestamp=datetime.now(),
            reaction_emoji=reaction_emoji,
            message=user_message,
        ),
    )

    db.write(
        "UPDATE agents SET last_user_message_time = %s WHERE id = %s",
        (
            datetime.now(),
            agent_id,
        ),
    )

    flows.inner_loop_step_node.run(runtime.shared)

    await runtime.event_queue.put(
        Event(AgentMessageEvent(message=runtime.shared["last_response"]))
    )

    runtime.user_message_count += 1

    if runtime.user_message_count % config.OPTIMISER_FREQUENCY_IN_USER_MESSAGES == 0:
        last_3_user_agent_turns = runtime.shared["conversation_history"][-(3 * 2) :]
        runtime.shared["conversation_history"] = runtime.shared["conversation_history"][
            : -(3 * 2)
        ]

        run_outer_loop(runtime, agent_id)

        runtime.shared["conversation_history"] = last_3_user_agent_turns

        await runtime.event_queue.put(
            Event(
                SystemEvent(
                    message="(SYSTEM) Personality optimisations and auxiliary memory updates complete. Interaction summary has been updated and older messages have been truncated.",
                )
            )
        )


@app.post("/sessions/{agent_id}")
async def new_session(
    agent_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if (
        current_user.id in sessions_by_user
        and agent_id in sessions_by_user[current_user.id]
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    matched_agents = db.read(
        "SELECT agents.agent_name, agents.last_user_message_time FROM agents WHERE agents.user_id = %s AND agents.id = %s",
        (current_user.id, agent_id),
    )

    if len(matched_agents) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    agent_name, last_user_message_time = matched_agents[0]

    if current_user.id not in sessions_by_user:
        sessions_by_user[current_user.id] = {}

    sessions_by_user[current_user.id][agent_id] = SessionRuntime(
        agent_id=agent_id,
        agent_name=agent_name,
        user_message_count=0,
        shared={
            "memory": memory.Memory.read_from_db(agent_id),
            "conversation_history": [],
        },
        event_queue=Queue(),
    )

    first_message = (
        "(SYSTEM) User has entered the conversation for the first time. Suggestion: introduce yourself/get to know the user."
        if not last_user_message_time
        else f"(SYSTEM) User has reentered the conversation (last user message {precisedelta(datetime.now() - last_user_message_time, minimum_unit='minutes')} ago)."
    )

    background_tasks.add_task(
        run_inner_loop,
        runtime=sessions_by_user[current_user.id][agent_id],
        agent_id=agent_id,
        user_message=first_message,
        reaction_emoji=None,
    )


@app.delete("/sessions/{agent_id}")
async def delete_session(
    agent_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not (
        current_user.id in sessions_by_user
        and agent_id in sessions_by_user[current_user.id]
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )

    runtime = sessions_by_user[current_user.id][agent_id]

    run_outer_loop(
        runtime=runtime,
        agent_id=agent_id,
    )

    await runtime.event_queue.put(Event(ExitEvent()))

    del sessions_by_user[current_user.id][agent_id]


@app.post("/sessions/{agent_id}/message")
async def send_message(
    agent_id: UUID,
    form_data: Annotated[UserMessageFormData, Form()],
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not (
        current_user.id in sessions_by_user
        and agent_id in sessions_by_user[current_user.id]
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )

    background_tasks.add_task(
        run_inner_loop,
        runtime=sessions_by_user[current_user.id][agent_id],
        agent_id=agent_id,
        user_message=form_data.message,
        reaction_emoji=form_data.reaction_emoji,
    )


@app.get("/sessions/{agent_id}/events")
async def stream_session_events(
    agent_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
) -> AsyncIterable[Event]:
    if not (
        current_user.id in sessions_by_user
        and agent_id in sessions_by_user[current_user.id]
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )

    event_queue = sessions_by_user[current_user.id][agent_id].event_queue
    while True:
        event = await event_queue.get()
        yield event
        event_queue.task_done()
        if event.root.event_type == "exit":
            break


# TODO: add semaphores


# if __name__ == "__main__":
#     print(
#         r"""
#     ___       __            __  _            ______                                  _
#    /   | ____/ /___ _____  / /_(_)   _____  / ____/___  ____ ___  ____  ____ _____  (_)___  ____
#   / /| |/ __  / __ `/ __ \/ __/ / | / / _ \/ /   / __ \/ __ `__ \/ __ \/ __ `/ __ \/ / __ \/ __ \
#  / ___ / /_/ / /_/ / /_/ / /_/ /| |/ /  __/ /___/ /_/ / / / / / / /_/ / /_/ / / / / / /_/ / / / /
# /_/  |_\__,_/\__,_/ .___/\__/_/ |___/\___/\____/\____/_/ /_/ /_/ .___/\__,_/_/ /_/_/\____/_/ /_/
#                  /_/                                          /_/
#
#     """,
#         flush=True,
#     )
#
#     agent_infos = [
#         (i, *agent_info)
#         for i, agent_info in enumerate(
#             db.read(
#                 """
# SELECT agents.id, core_personality.name, agents.created_at, agents.last_user_message_time FROM agents
# INNER JOIN core_personality ON agents.id = core_personality.agent_id
#     """
#             )
#         )
#     ]
#     for i, agent_id, name, created_at, last_user_message_time in agent_infos:
#         print(
#             f"{i+1}) {name} (id {agent_id}, created at {created_at}, last user message at {last_user_message_time})",
#             flush=True,
#         )
#
#     print(
#         'Enter number corresponding to agent you wish to chat with ("new" for new agent)\n> ',
#         end="",
#         flush=True,
#     )
#
#     choice = input().strip()
#     if choice == "new":
#         agent_id = uuid4()
#
#         memory_data = memory.DEFAULT_MEMORY
#
#         db.write("INSERT INTO agents (id) VALUES (%s)", (agent_id,))
#         memory_data.insert_into_db(agent_id)
#         last_user_message_time = None
#         agent_name = memory_data.core_personality.name
#     else:
#         choice_int = int(choice) - 1
#         assert 0 <= choice_int < len(agent_infos), "Invalid choice"
#         agent_id = agent_infos[choice_int][1]
#         last_user_message_time = agent_infos[choice_int][4]
#         agent_name = agent_infos[choice_int][2]
#
#     interact_with_agent(agent_id, last_user_message_time, agent_name)
