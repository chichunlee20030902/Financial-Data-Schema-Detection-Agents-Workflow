# Financial Data Pipeline — Claude Code 專案指令

## 專案目標

建立一個 multi-agent 系統，讓使用者上傳 CSV 或 Excel 檔案，由多個 Agent 協作完成：
1. 自動偵測資料結構（Schema Detection）
2. 自動清理資料（Data Cleaning）
3. 將資料寫入 MySQL
4. 驗證寫入結果

整個流程由一個 Supervisor Agent 監督每個步驟的品質。

---

## 檔案結構

請按照以下結構建立專案：

```
project/
│
├── main.py                  # 主程式，控制整個流程
├── config.py                # API key、DB 設定
│
├── agents/
│   ├── base_agent.py        # 所有 Agent 的基礎類別
│   ├── supervisor.py        # Supervisor Agent
│   ├── schema_detector.py   # Agent 1
│   ├── data_cleaner.py      # Agent 2
│   ├── sql_writer.py        # Agent 3
│   └── validator.py         # Agent 4
│
└── utils/
    ├── file_loader.py       # 讀取 CSV / Excel
    ├── db_connector.py      # MySQL 連線與操作
    └── logger.py            # 記錄所有修改與問題
```

---

## 技術棧

- Python 3.10+
- `anthropic` — Claude API SDK
- `pandas` — 資料處理
- `mysql-connector-python` — MySQL 連線
- `openpyxl` — 讀取 Excel 檔案

安裝指令：
```bash
pip install anthropic pandas mysql-connector-python openpyxl
```

---

## 設定檔 config.py

```python
# config.py
ANTHROPIC_API_KEY = "你的_API_KEY"

DB_CONFIG = {
    "host": "localhost",
    "user": "你的_DB_USER",
    "password": "你的_DB_PASSWORD",
    "database": "你的_DB_NAME"
}

MODEL = "claude-opus-4-5"
MAX_TOKENS = 2048
MAX_REVIEW_ROUNDS = 3  # Supervisor 最多跟每個 Agent 討論幾輪
```

---

## 各 Agent 的職責與 System Prompt

### base_agent.py
所有 Agent 繼承的基礎類別，包含：
- `__init__(self, name, system_prompt)` — 初始化 Agent
- `run(self, user_message, context=None)` — 呼叫 Claude API，回傳文字結果
- 使用 `config.py` 的 MODEL 和 MAX_TOKENS

### supervisor.py
**角色：** 監督每個步驟的品質，與負責的 Agent 討論，確認結果合格後才交接給下一步。

**System Prompt 重點：**
- 你是一個資深的資料工程師，負責監督整個資料處理流程
- 你會收到每個 Agent 的輸出，判斷是否合格
- 如果不合格，給出具體的改善建議，要求 Agent 重做
- 如果合格，輸出 `{"approved": true, "summary": "..."}` 的 JSON
- 如果不合格，輸出 `{"approved": false, "feedback": "..."}` 的 JSON
- 永遠只回傳 JSON，不加任何說明文字

**方法：**
- `review(self, agent_name, agent_output)` — 審查 Agent 的輸出，回傳 JSON

### schema_detector.py
**角色：** 分析 DataFrame 的結構，找出所有潛在問題。

**System Prompt 重點：**
- 你是一個資料分析專家，專門處理金融資料
- 輸入：DataFrame 的 schema 資訊（欄位名稱、型別、樣本值、缺失值數量）
- 輸出 JSON 格式：
```json
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
}
```

**方法：**
- `detect(self, df)` — 接收 DataFrame，回傳 schema 分析 JSON

### data_cleaner.py
**角色：** 根據 schema 分析結果，自動清理資料。能修的就修，修不了的記錄下來。

**System Prompt 重點：**
- 你是一個資料清理專家
- 輸入：schema 分析結果 + DataFrame 的前20行樣本
- 輸出 JSON 格式：
```json
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
```
- 實際清理操作用 pandas 在 Python 端執行，LLM 只負責規劃

**方法：**
- `plan(self, schema_result, df_sample)` — 回傳清理計畫 JSON
- `execute(self, df, cleaning_plan)` — 根據計畫執行 pandas 清理操作，回傳清理後的 DataFrame

### sql_writer.py
**角色：** 根據清理後的 schema，生成建表語法和資料寫入語法。

**System Prompt 重點：**
- 你是一個 MySQL 資料庫專家
- 輸入：清理後的 schema 資訊
- 輸出 JSON 格式：
```json
{
  "table_name": "建議的資料表名稱",
  "create_table_sql": "CREATE TABLE ... 完整語法",
  "column_mapping": {
    "原始欄位名": "SQL欄位名"
  }
}
```
- SQL 語法必須符合 MySQL 規範
- 資料型別對應：date→DATE, float→DECIMAL(18,6), int→INT, string→VARCHAR(255)

**方法：**
- `generate(self, schema_result)` — 回傳 SQL 相關 JSON

### validator.py
**角色：** 資料寫入 MySQL 後，驗證寫入結果是否正確。

**System Prompt 重點：**
- 你是一個資料品質驗證專家
- 輸入：原始 DataFrame 資訊 + 寫入後的資料庫查詢結果
- 輸出 JSON 格式：
```json
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
}
```

**方法：**
- `validate(self, original_df, table_name, db_connector)` — 執行驗證，回傳 JSON

---

## utils 說明

### file_loader.py
- `load(file_path)` — 自動判斷 CSV 或 Excel，回傳 DataFrame
- `get_schema_info(df)` — 回傳 schema 文字描述，供 Agent 使用：
  - 總行數、總欄數
  - 每個欄位：名稱、型別、樣本值（前3筆）、缺失值數量

### db_connector.py
- `connect()` — 使用 config.py 連線 MySQL
- `create_table(create_sql)` — 執行建表語法
- `insert_dataframe(df, table_name, column_mapping)` — 批次寫入 DataFrame
- `query(sql)` — 執行查詢，回傳結果

### logger.py
記錄整個流程，包含：
- Schema Detection 的發現
- Data Cleaning 的每一個修改（欄位、修改內容、原因）
- 需要使用者確認的問題
- Validator 的驗證結果
- 提供 `print_report()` 方法在最後輸出完整報告

---

## main.py 流程

```python
# 主流程邏輯（用 pseudocode 說明）

1. 讀取使用者輸入的檔案路徑
2. 用 file_loader 載入 DataFrame
3. 初始化所有 Agent 和 Logger

# Step 1: Schema Detection
4. schema_detector.detect(df) → schema_result
5. supervisor 與 schema_detector 討論（最多 MAX_REVIEW_ROUNDS 輪）
   - supervisor.review("schema_detector", schema_result)
   - 如果 approved=false，把 feedback 傳回 schema_detector 重做
   - 如果 approved=true，進入下一步
6. logger 記錄 schema 結果

# Step 2: Data Cleaning
7. data_cleaner.plan(schema_result, df.head(20)) → cleaning_plan
8. supervisor 與 data_cleaner 討論
9. 如果有 requires_user_input，印出問題讓使用者回答
10. data_cleaner.execute(df, cleaning_plan) → cleaned_df
11. logger 記錄所有清理操作

# Step 3: SQL Writing
12. sql_writer.generate(schema_result) → sql_result
13. supervisor 與 sql_writer 討論
14. db_connector.create_table(sql_result["create_table_sql"])
15. db_connector.insert_dataframe(cleaned_df, sql_result["table_name"], sql_result["column_mapping"])

# Step 4: Validation
16. validator.validate(cleaned_df, sql_result["table_name"], db_connector) → validation_result
17. supervisor 與 validator 討論
18. 如果 passed=false，印出問題供人工處理

# 最後
19. logger.print_report()
```

---

## Supervisor 討論迴圈的實作方式

```python
def supervised_step(supervisor, agent_name, agent_output, max_rounds=3):
    for round in range(max_rounds):
        review = supervisor.review(agent_name, agent_output)
        if review["approved"]:
            return agent_output
        else:
            # 把 feedback 傳回給 agent 重做
            agent_output = agent.revise(review["feedback"])
    return agent_output  # 超過輪數就直接過
```

---

## 注意事項

1. 所有 LLM 回傳的內容都預期是 JSON，請用 `json.loads()` 解析，並加上 try/except 處理解析失敗的情況
2. 如果 JSON 解析失敗，把原始回傳文字印出來 debug
3. MySQL 的敏感資訊（密碼）不要 hardcode，從 config.py 讀取
4. 每次呼叫 Claude API 前，印出 `[Agent名稱] 執行中...` 讓使用者知道進度
5. 整個流程結束後，印出完整的修改報告

---

## 測試用資料

建立 `test_data.csv` 來測試：

```csv
date,ticker,direction,quantity,price,broker
2024-01-02,AAPL,BUY,100,185.2,Goldman
2024-01-02,TSLA,BUY,50,248.5,Morgan
2024-01-03,AAPL,SELL,30,187.0,Goldman
2024-01-03,2330.TW,BUY,1000,580.0,CTBC
2024-01-04,,SELL,20,245.0,Morgan
2024-01-04,NVDA,BUY,200,not_a_number,Goldman
```

注意：第5行 ticker 是空的，第6行 price 是非數字，用來測試 Data Cleaner。
