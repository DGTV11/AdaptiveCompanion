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
                message="(SYSTEM) User has entered the conversation for the first time"
            )
        ],
    }
    flows.inner_loop_step_node.run(shared)
    print(f"Agent: {shared['response']}", end="\n\n")

    user_message = ""
    while user_message != "quit":  # TODO: add optimiser outer loop
        user_message = input(
            'User (enter "/quit" to quit, "/memory" to view memory from agent perspective): '
        ).strip()

        match user_message:
            case "/quit":
                break
            case "/memory":
                print(repr(shared["memory"]), end="\n\n")
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
