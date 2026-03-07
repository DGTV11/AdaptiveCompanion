from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from humanize import precisedelta

import config
import db
import flows
import memory
import messages


def run_inner_loop(shared: Dict[str, Any], agent_id: UUID, user_message: str):
    shared["conversation_history"].append(
        messages.UserMessage(message=user_message),
    )
    flows.inner_loop_step_node.run(shared)

    db.write(
        "UPDATE agents SET last_user_message_time = %s WHERE id = %s",
        (
            datetime.now(),
            agent_id,
        ),
    )


def run_outer_loop(shared: Dict[str, Any], agent_id: UUID):
    flows.outer_loop_optimiser_step_node.run(shared)
    flows.outer_loop_summariser_step_node.run(shared)

    shared["memory"].update_db(agent_id)


def interact_with_agent(
    agent_id: UUID, last_user_message_time: Optional[datetime], agent_name: str
):
    print("Generating first agent message...", flush=True)
    shared = {
        "memory": memory.Memory.read_from_db(agent_id),
        "conversation_history": [],
    }

    first_message = (
        "(SYSTEM) User has entered the conversation for the first time. Suggestion: introduce yourself/get to know the user."
        if not last_user_message_time
        else f"(SYSTEM) User has reentered the conversation (last user message {precisedelta(datetime.now() - last_user_message_time, minimum_unit='minutes')} ago)."
    )
    print(first_message, flush=True)

    run_inner_loop(
        shared,
        agent_id,
        first_message,
    )
    print(f"{agent_name}: {shared['message']}", end="\n\n", flush=True)

    user_message = ""
    user_message_count = 0
    try:
        while user_message != "quit":
            print('You (enter "/quit" to quit, "/help" for help): ', end="", flush=True)
            user_message = input().strip()

            match user_message:
                case "":
                    continue
                case "/quit":
                    break
                case "/help":
                    print(
                        """
    /help - display this help message
    /quit - quit
    /memory - display agent memory view
    /last_response - display last agent full response
                    """,
                        end="\n\n",
                        flush=True,
                    )
                    continue
                case "/memory":
                    print(repr(shared["memory"]), end="\n\n", flush=True)
                    continue
                case "/last_response":
                    if len(shared["conversation_history"]) == 0:
                        print("No last agent full response", flush=True)
                    else:
                        print(shared["last_response"], flush=True)
                    continue
                case _:
                    user_message = f"(USER) {user_message}"
                    if (
                        user_message_count > 0
                        and user_message_count
                        % config.OPTIMISER_FREQUENCY_IN_USER_MESSAGES
                        == 0
                    ):
                        user_message = f"(SYSTEM) Personality optimisations and auxiliary memory updates complete.\n\n{user_message}"

                    run_inner_loop(
                        shared,
                        agent_id,
                        user_message,
                    )
                    print(f"{agent_name}: {shared['message']}", end="\n\n", flush=True)

            user_message_count += 1
            if user_message_count % config.OPTIMISER_FREQUENCY_IN_USER_MESSAGES == 0:
                run_outer_loop(shared, agent_id)

                shared["conversation_history"] = shared["conversation_history"][-2:]

                print(
                    "(SYSTEM) Personality optimisations and auxiliary memory updates complete.",
                    flush=True,
                )
    except KeyboardInterrupt:
        pass

    print("Exiting...", flush=True)

    run_outer_loop(shared, agent_id)

    print(
        "(SYSTEM) Personality optimisations and auxiliary memory updates complete.",
        flush=True,
    )


if __name__ == "__main__":
    print(
        """
 █████╗ ██████╗  █████╗ ██████╗ ████████╗██╗██╗   ██╗███████╗ ██████╗ ██████╗ ███╗   ███╗██████╗  █████╗ ███╗   ██╗██╗ ██████╗ ███╗   ██╗
██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██║██║   ██║██╔════╝██╔════╝██╔═══██╗████╗ ████║██╔══██╗██╔══██╗████╗  ██║██║██╔═══██╗████╗  ██║
███████║██║  ██║███████║██████╔╝   ██║   ██║██║   ██║█████╗  ██║     ██║   ██║██╔████╔██║██████╔╝███████║██╔██╗ ██║██║██║   ██║██╔██╗ ██║
██╔══██║██║  ██║██╔══██║██╔═══╝    ██║   ██║╚██╗ ██╔╝██╔══╝  ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══██║██║╚██╗██║██║██║   ██║██║╚██╗██║
██║  ██║██████╔╝██║  ██║██║        ██║   ██║ ╚████╔╝ ███████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ██║  ██║██║ ╚████║██║╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝        ╚═╝   ╚═╝  ╚═══╝  ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝

    """,
        flush=True,
    )

    agent_infos = [
        (i, *agent_info)
        for i, agent_info in enumerate(
            db.read(
                """
SELECT agents.id, core_personality.name, agents.created_at, agents.last_user_message_time FROM agents
INNER JOIN core_personality ON agents.id = core_personality.agent_id
    """
            )
        )
    ]
    for i, agent_id, name, created_at, last_user_message_time in agent_infos:
        print(
            f"{i+1}) {name} (id {agent_id}, created at {created_at}, last user message at {last_user_message_time})",
            flush=True,
        )

    print(
        'Enter number corresponding to agent you wish to chat with ("new" for new agent)\n> ',
        end="",
        flush=True,
    )

    choice = input().strip()
    if choice == "new":
        agent_id = uuid4()

        memory_data = memory.DEFAULT_MEMORY

        db.write("INSERT INTO agents (id) VALUES (%s)", (agent_id,))
        memory_data.insert_into_db(agent_id)
        last_user_message_time = None
        agent_name = memory_data.core_personality.name
    else:
        choice_int = int(choice) - 1
        assert 0 <= choice_int < len(agent_infos), "Invalid choice"
        agent_id = agent_infos[choice_int][1]
        last_user_message_time = agent_infos[choice_int][4]
        agent_name = agent_infos[choice_int][2]

    interact_with_agent(agent_id, last_user_message_time, agent_name)
