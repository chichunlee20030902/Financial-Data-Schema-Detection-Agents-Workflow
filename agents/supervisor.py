import json
from agents.base_agent import BaseAgent

SUPERVISOR_SYSTEM_PROMPT = """你是一個資深的資料工程師，負責監督整個資料處理流程。
你會收到每個 Agent 的輸出，判斷是否合格。
如果不合格，給出具體的改善建議，要求 Agent 重做。
如果合格，輸出 {"approved": true, "summary": "..."} 的 JSON。
如果不合格，輸出 {"approved": false, "feedback": "..."} 的 JSON。
永遠只回傳 JSON，不加任何說明文字。"""


class SupervisorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Supervisor", SUPERVISOR_SYSTEM_PROMPT)

    def review(self, agent_name: str, agent_output: str) -> dict:
        user_message = f"請審查 {agent_name} 的輸出結果：\n\n{agent_output}"
        response = self.run(user_message)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"[Supervisor] JSON 解析失敗，原始回傳：\n{response}")
            return {"approved": False, "feedback": "回傳格式錯誤，請重試"}
