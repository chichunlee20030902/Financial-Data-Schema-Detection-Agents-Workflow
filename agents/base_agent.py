import anthropic
import config


class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def run(self, user_message: str, context: str = None) -> str:
        print(f"[{self.name}] 執行中...")

        if context:
            full_message = f"{context}\n\n{user_message}"
        else:
            full_message = user_message

        message = self.client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": full_message}
            ]
        )

        return message.content[0].text
