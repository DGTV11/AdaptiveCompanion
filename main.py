import config
import flows
import memory
import messages


def main():
    print("Generating first agent message...")
    shared = {
        "memory": memory.DEFAULT_MEMORY,
        "conversation_history": [
            messages.UserMessage(
                message="(SYSTEM) User has entered the conversation for the first time. Suggestion: introduce yourself/get to know the user."
            )
        ],
    }
    flows.inner_loop_step_node.run(shared)
    print(f"Agent: {shared['response']}", end="\n\n")

    user_message = ""
    while (
        user_message != "quit"
    ):  # TODO: add optimiser outer loop (runs every N user messages + after user leaves convo)
        user_message = input('User (enter "/quit" to quit, "/help" for help): ').strip()

        match user_message:
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
                )
                continue
            case "/memory":
                print(repr(shared["memory"]), end="\n\n")
                continue
            case "/last_response":
                if len(shared["conversation_history"]) == 0:
                    print("No last agent full response")
                else:
                    print(shared["conversation_history"][-1])
                continue
            case _:
                shared["conversation_history"].append(
                    messages.UserMessage(message=user_message)
                )
                flows.inner_loop_step_node.run(shared)
                print(f"Agent: {shared['response']}", end="\n\n")

    # TODO: add persistence using postgres + summarisation loop


if __name__ == "__main__":
    main()
