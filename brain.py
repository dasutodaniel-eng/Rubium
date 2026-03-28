import openai
import anthropic
import google.generativeai as genai

class Brain:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager

        # Load config
        config = self.memory_manager.load_config()
        self.provider = config.get("provider", "openai").lower()
        self.api_key = config.get("api_key", "")

        # Initialize clients based on provider
        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=self.api_key)
            self.model = "gpt-4o-mini"
        elif self.provider == "deepseek":
            # DeepSeek uses the OpenAI compatible API
            self.client = openai.OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
            self.model = "deepseek-chat"
        elif self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-haiku-20240307"
        elif self.provider == "google":
            genai.configure(api_key=self.api_key)
            # system prompt instruction in gemini works best in the model config
            self.model = "gemini-1.5-flash"
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def set_system_prompt(self, system_prompt):
        """Sets an initial system message to define the assistant's persona."""
        self.system_prompt = system_prompt

        history = self.memory_manager.load_history()

        # Check if the first message is already a system prompt
        if not history or history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": system_prompt})
            self.memory_manager.save_history(history)
        else:
            # Update the existing system prompt
            history[0]["content"] = system_prompt
            self.memory_manager.save_history(history)

    def process_message(self, user_input, stream=False):
        """Processes the user input through the chosen cloud LLM."""
        if not self.api_key:
            return "Error: No API key configured. Please clear memory/config and restart."

        # 1. Add user message to memory
        self.memory_manager.add_message("user", user_input)

        # 2. Retrieve entire conversational history
        messages = self.memory_manager.load_history()

        try:
            full_reply = ""
            if self.provider in ["openai", "deepseek"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=stream
                )
                if stream:
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            print(content, end='', flush=True)
                            full_reply += content
                    print()
                else:
                    full_reply = response.choices[0].message.content

            elif self.provider == "anthropic":
                # Anthropic doesn't include the 'system' role in the messages array
                # It passes it as a separate parameter
                system_msg = ""
                anthropic_messages = []
                for msg in messages:
                    if msg["role"] == "system":
                        system_msg = msg["content"]
                    else:
                        anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

                if stream:
                    with self.client.messages.stream(
                        model=self.model,
                        max_tokens=1024,
                        system=system_msg,
                        messages=anthropic_messages
                    ) as response_stream:
                        for text in response_stream.text_stream:
                            print(text, end='', flush=True)
                            full_reply += text
                    print()
                else:
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=1024,
                        system=system_msg,
                        messages=anthropic_messages
                    )
                    full_reply = response.content[0].text

            elif self.provider == "google":
                # Gemini doesn't use the 'system' role in the messages history
                # It uses 'user' and 'model'
                gemini_messages = []
                system_instruction = None

                for msg in messages:
                    if msg["role"] == "system":
                        system_instruction = msg["content"]
                    elif msg["role"] == "user":
                        gemini_messages.append({"role": "user", "parts": [msg["content"]]})
                    elif msg["role"] == "assistant":
                        gemini_messages.append({"role": "model", "parts": [msg["content"]]})

                model = genai.GenerativeModel(
                    model_name=self.model,
                    system_instruction=system_instruction
                )

                # Create a chat session with the previous history
                # We pop the last user message to use as the prompt
                prompt = gemini_messages.pop()["parts"][0]

                chat = model.start_chat(history=gemini_messages)

                if stream:
                    response = chat.send_message(prompt, stream=True)
                    for chunk in response:
                        print(chunk.text, end='', flush=True)
                        full_reply += chunk.text
                    print()
                else:
                    response = chat.send_message(prompt)
                    full_reply = response.text

            # 4. Save the assistant's final reply to memory
            self.memory_manager.add_message("assistant", full_reply)

            return full_reply

        except Exception as e:
            error_msg = f"API Error ({self.provider}): {str(e)}"
            print(f"\n{error_msg}")
            return error_msg
