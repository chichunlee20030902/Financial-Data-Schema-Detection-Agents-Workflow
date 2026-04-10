import json
from agents.base_agent import BaseAgent

SQL_WRITER_SYSTEM_PROMPT = """你是一個 MySQL 資料庫專家。
輸入：清理後的 schema 資訊。
輸出必須是以下 JSON 格式，不加任何說明文字：
{
  "table_name": "建議的資料表名稱",
  "create_table_sql": "CREATE TABLE ... 完整語法",
  "column_mapping": {
    "原始欄位名": "SQL欄位名"
  }
}
SQL 語法必須符合 MySQL 規範。
資料型別對應：date→DATE, float→DECIMAL(18,6), int→INT, string→VARCHAR(255)。"""


class SQLWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__("SQLWriter", SQL_WRITER_SYSTEM_PROMPT)
        self._last_schema = ""

    def generate(self, schema_result: dict) -> dict:
        schema_str = json.dumps(schema_result, ensure_ascii=False, indent=2)
        self._last_schema = schema_str

        response = self.run(f"請根據以下 schema 生成 MySQL 建表語法：\n\n{schema_str}")

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"[SQLWriter] JSON 解析失敗，原始回傳：\n{response}")
            return {"table_name": "", "create_table_sql": "", "column_mapping": {}}

    def revise(self, feedback: str) -> dict:
        response = self.run(
            f"請根據以下意見重新生成 SQL：\n{feedback}\n\n原始 schema：\n{self._last_schema}"
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"[SQLWriter] JSON 解析失敗，原始回傳：\n{response}")
            return {"table_name": "", "create_table_sql": "", "column_mapping": {}}
