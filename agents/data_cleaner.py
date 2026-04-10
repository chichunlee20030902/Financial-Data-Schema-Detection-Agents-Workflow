import json
import pandas as pd
from agents.base_agent import BaseAgent

DATA_CLEANER_SYSTEM_PROMPT = """你是一個資料清理專家。
輸入：schema 分析結果 + DataFrame 的前20行樣本。
輸出必須是以下 JSON 格式，不加任何說明文字：
{
  "cleaning_plan": [
    {
      "column": "欄位名稱",
      "action": "convert_type/fill_null/drop_column/flag_for_review",
      "detail": "具體做什麼",
      "auto_fixable": true
    }
  ],
  "requires_user_input": [
    {
      "column": "欄位名稱",
      "issue": "問題描述",
      "options": ["選項1", "選項2"]
    }
  ]
}
實際清理操作用 pandas 在 Python 端執行，你只負責規劃。"""


class DataCleanerAgent(BaseAgent):
    def __init__(self):
        super().__init__("DataCleaner", DATA_CLEANER_SYSTEM_PROMPT)
        self._last_input = ""

    def plan(self, schema_result: dict, df_sample: pd.DataFrame) -> dict:
        sample_str = df_sample.to_string()
        schema_str = json.dumps(schema_result, ensure_ascii=False, indent=2)
        self._last_input = f"Schema 分析結果：\n{schema_str}\n\nDataFrame 前20行：\n{sample_str}"

        response = self.run(f"請根據以下資訊制定清理計畫：\n\n{self._last_input}")

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"[DataCleaner] JSON 解析失敗，原始回傳：\n{response}")
            return {"cleaning_plan": [], "requires_user_input": []}

    def revise(self, feedback: str) -> dict:
        response = self.run(
            f"請根據以下意見重新制定清理計畫：\n{feedback}\n\n原始資料：\n{self._last_input}"
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"[DataCleaner] JSON 解析失敗，原始回傳：\n{response}")
            return {"cleaning_plan": [], "requires_user_input": []}

    def execute(self, df: pd.DataFrame, cleaning_plan: dict) -> pd.DataFrame:
        cleaned_df = df.copy()

        for step in cleaning_plan.get("cleaning_plan", []):
            if not step.get("auto_fixable", False):
                continue

            col = step["column"]
            action = step["action"]

            if col not in cleaned_df.columns:
                continue

            if action == "convert_type":
                detail = step.get("detail", "")
                if "date" in detail.lower():
                    cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors="coerce")
                elif "float" in detail.lower():
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce")
                elif "int" in detail.lower():
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce").astype("Int64")

            elif action == "fill_null":
                detail = step.get("detail", "")
                if "mean" in detail.lower() and cleaned_df[col].dtype in ["float64", "int64"]:
                    cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mean())
                elif "0" in detail:
                    cleaned_df[col] = cleaned_df[col].fillna(0)
                else:
                    cleaned_df[col] = cleaned_df[col].fillna("UNKNOWN")

            elif action == "drop_column":
                cleaned_df = cleaned_df.drop(columns=[col])

        return cleaned_df
