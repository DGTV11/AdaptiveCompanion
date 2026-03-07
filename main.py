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
    print(f"Agent: {shared['message']}", end="\n\n")

    user_message = ""
    user_message_count = 0
    while user_message != "quit":
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
                    print(shared["last_response"])
                continue
            case _:
                user_message = f"(USER) {user_message}"
                if (
                    user_message_count > 0
                    and user_message_count % config.OPTIMISER_FREQUENCY_IN_USER_MESSAGES
                    == 0
                ):
                    user_message = f"(SYSTEM) Personality optimisations and auxiliary memory updates complete.\n\n{user_message}"

                shared["conversation_history"].append(
                    messages.UserMessage(message=user_message)
                )
                flows.inner_loop_step_node.run(shared)
                print(f"Agent: {shared['message']}", end="\n\n")

        user_message_count += 1
        if user_message_count % config.OPTIMISER_FREQUENCY_IN_USER_MESSAGES == 0:
            flows.outer_loop_optimiser_step_node.run(shared)
            flows.outer_loop_summariser_step_node.run(shared)

            shared["conversation_history"] = shared["conversation_history"][-2:]

            print(
                "(SYSTEM) Personality optimisations and auxiliary memory updates complete."
            )

    # TODO: add persistence using postgres


if __name__ == "__main__":
    main()
