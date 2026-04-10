import json
import pandas as pd
from agents.base_agent import BaseAgent

VALIDATOR_SYSTEM_PROMPT = """你是一個資料品質驗證專家。
輸入：原始 DataFrame 資訊 + 寫入後的資料庫查詢結果。
輸出必須是以下 JSON 格式，不加任何說明文字：
{
  "passed": true,
  "checks": [
    {
      "check_name": "row_count_match",
      "expected": 100,
      "actual": 100,
      "passed": true
    }
  ],
  "issues": []
}"""


class ValidatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Validator", VALIDATOR_SYSTEM_PROMPT)
        self._last_input = ""

    def validate(self, original_df: pd.DataFrame, table_name: str, db_connector) -> dict:
        row_count = len(original_df)
        columns = list(original_df.columns)

        db_rows = db_connector.query(f"SELECT COUNT(*) as cnt FROM {table_name}")
        db_count = db_rows[0]["cnt"] if db_rows else 0

        sample_rows = db_connector.query(f"SELECT * FROM {table_name} LIMIT 5")

        input_str = (
            f"原始 DataFrame：\n"
            f"- 總行數：{row_count}\n"
            f"- 欄位：{columns}\n\n"
            f"資料庫查詢結果：\n"
            f"- 資料表：{table_name}\n"
            f"- 寫入行數：{db_count}\n"
            f"- 前5行樣本：{json.dumps(sample_rows, ensure_ascii=False, default=str)}"
        )
        self._last_input = input_str

        response = self.run(f"請驗證以下資料寫入結果：\n\n{input_str}")

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"[Validator] JSON 解析失敗，原始回傳：\n{response}")
            return {"passed": False, "checks": [], "issues": ["解析失敗"]}

    def revise(self, feedback: str) -> dict:
        response = self.run(
            f"請根據以下意見重新驗證：\n{feedback}\n\n原始資料：\n{self._last_input}"
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"[Validator] JSON 解析失敗，原始回傳：\n{response}")
            return {"passed": False, "checks": [], "issues": ["解析失敗"]}
