import ollama

class Brain:
    def __init__(self, memory_manager, model="gemma2:2b"):
        self.memory_manager = memory_manager
        self.model = model

    def set_system_prompt(self, system_prompt):
        """Sets an initial system message to define the assistant's persona."""
        # Ensure we don't duplicate system prompts
        history = self.memory_manager.load_history()

        # Check if the first message is already a system prompt
        if not history or history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": system_prompt})
            self.memory_manager.save_history(history)
        else:
            # Update the existing system prompt
            history[0]["content"] = system_prompt
            self.memory_manager.save_history(history)

    def process_message(self, user_input, stream=True):
        """Processes the user input through the LLM using conversational history."""
        # 1. Add user message to memory
        self.memory_manager.add_message("user", user_input)

        # 2. Retrieve entire conversational history
        messages = self.memory_manager.load_history()

        # 3. Stream the response from the local LLM
        try:
            if stream:
                response = ollama.chat(model=self.model, messages=messages, stream=True)

                full_reply = ""
                for chunk in response:
                    content = chunk['message']['content']
                    print(content, end='', flush=True)
                    full_reply += content

                print() # Print a newline at the end of the streaming response
            else:
                response = ollama.chat(model=self.model, messages=messages, stream=False)
                full_reply = response['message']['content']

            # 4. Save the assistant's final reply to memory
            self.memory_manager.add_message("assistant", full_reply)

            return full_reply

        except Exception as e:
            error_msg = f"\nError communicating with Ollama: {e}"
            print(error_msg)
            return error_msg
