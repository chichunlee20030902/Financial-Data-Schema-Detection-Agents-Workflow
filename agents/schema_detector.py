import json
import pandas as pd
from agents.base_agent import BaseAgent

SCHEMA_DETECTOR_SYSTEM_PROMPT = """你是一個資料分析專家，專門處理金融資料。
輸入：DataFrame 的 schema 資訊（欄位名稱、型別、樣本值、缺失值數量）。
輸出必須是以下 JSON 格式，不加任何說明文字：
{
  "columns": [
    {
      "name": "欄位名稱",
      "detected_type": "date/float/int/string/unknown",
      "issues": ["問題描述1", "問題描述2"],
      "suggestion": "建議處理方式"
    }
  ],
  "overall_issues": ["整體資料問題"],
  "can_proceed": true
}"""


class SchemaDetectorAgent(BaseAgent):
    def __init__(self):
        super().__init__("SchemaDetector", SCHEMA_DETECTOR_SYSTEM_PROMPT)
        self._last_schema_info = ""

    def detect(self, df: pd.DataFrame) -> dict:
        from utils.file_loader import get_schema_info
        schema_info = get_schema_info(df)
        self._last_schema_info = schema_info

        response = self.run(f"請分析以下 DataFrame 的 schema：\n\n{schema_info}")

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"[SchemaDetector] JSON 解析失敗，原始回傳：\n{response}")
            return {"columns": [], "overall_issues": ["解析失敗"], "can_proceed": False}

    def revise(self, feedback: str) -> dict:
        response = self.run(
            f"請根據以下意見重新分析：\n{feedback}\n\n原始資料：\n{self._last_schema_info}"
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"[SchemaDetector] JSON 解析失敗，原始回傳：\n{response}")
            return {"columns": [], "overall_issues": ["解析失敗"], "can_proceed": False}
