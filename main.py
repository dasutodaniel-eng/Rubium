import sys
from memory import MemoryManager
from brain import Brain

def main():
    print("Initializing Symbiote...")
    memory_manager = MemoryManager()
    brain = Brain(memory_manager, model="gemma2:2b")

    # Establish base persona/instructions
    system_prompt = (
        "You are a highly advanced AI Symbiote and personal assistant, akin to Jarvis. "
        "You are intelligent, resourceful, and capable of learning from interactions. "
        "Keep your responses concise and helpful. You speak Russian by default."
    )
    brain.set_system_prompt(system_prompt)

    print("\nSymbiote is online. Type 'exit' or 'quit' to terminate.")
    print("Type 'clear' to reset memory.")

    while True:
        try:
            user_input = input("\nUser: ").strip()
            if not user_input:
                continue

            lower_input = user_input.lower()
            if lower_input in ["exit", "quit"]:
                print("Symbiote going offline. Goodbye.")
                break
            elif lower_input == "clear":
                memory_manager.clear_history()
                brain.set_system_prompt(system_prompt)
                print("Memory cleared.")
                continue

            print("Symbiote: ", end="", flush=True)
            brain.process_message(user_input)

        except KeyboardInterrupt:
            print("\nSymbiote going offline. Goodbye.")
            sys.exit(0)
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
