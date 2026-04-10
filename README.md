# Financial Data Pipeline — Multi-Agent System

一個基於 Claude API 的 Multi-Agent 系統，自動處理 CSV / Excel 金融資料，完成 Schema 偵測、資料清理、寫入 MySQL、驗證等完整流程。

---

## 專案架構

```
Schema_Detection_Agents/
├── main.py                  # 主程式，控制整個流程
├── config.py                # API Key、資料庫設定
├── agents/
│   ├── base_agent.py        # 所有 Agent 的基礎類別
│   ├── supervisor.py        # 監督 Agent，審查每個步驟
│   ├── schema_detector.py   # Agent 1：偵測資料結構
│   ├── data_cleaner.py      # Agent 2：自動清理資料
│   ├── sql_writer.py        # Agent 3：生成 MySQL 建表語法
│   └── validator.py         # Agent 4：驗證寫入結果
└── utils/
    ├── file_loader.py       # 讀取 CSV / Excel
    ├── db_connector.py      # MySQL 連線與操作
    └── logger.py            # 記錄所有修改，產生完整報告
```

---

## 流程說明

```
上傳 CSV/Excel
      ↓
Schema Detection（偵測欄位型別與問題）
      ↓ Supervisor 審查
Data Cleaning（自動清理髒資料）
      ↓ Supervisor 審查
SQL Writing（生成建表語法並寫入 MySQL）
      ↓ Supervisor 審查
Validation（驗證寫入結果）
      ↓
輸出完整報告
```

每個步驟都由 **Supervisor Agent** 審查，不合格會要求重做（最多 3 輪）。

---

## 環境需求

- Python 3.10+
- MySQL 8.0+
- Anthropic API Key（需另外購買額度）

---

## 安裝步驟

**1. 安裝 Python 套件**

```bash
pip install anthropic pandas mysql-connector-python openpyxl
```

**2. 建立 MySQL 資料庫**

登入 MySQL 後執行：

```sql
CREATE DATABASE schema_detection;
```

**3. 設定 config.py**

開啟 `config.py`，填入你的設定：

```python
ANTHROPIC_API_KEY = "你的_API_KEY"  # 從 console.anthropic.com 取得

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "你的_MySQL_密碼",
    "database": "schema_detection"
}
```

---

## 使用方式

執行主程式：

```bash
python main.py
```

依照提示輸入 CSV 或 Excel 檔案路徑，程式會自動完成所有步驟並輸出報告。

---

## 測試資料

專案附有 `test_data.csv`，包含故意設計的髒資料：

```
date,ticker,direction,quantity,price,broker
2024-01-02,AAPL,BUY,100,185.2,Goldman
2024-01-02,TSLA,BUY,50,248.5,Morgan
2024-01-03,AAPL,SELL,30,187.0,Goldman
2024-01-03,2330.TW,BUY,1000,580.0,CTBC
2024-01-04,,SELL,20,245.0,Morgan        ← ticker 為空
2024-01-04,NVDA,BUY,200,not_a_number,Goldman  ← price 為非數字
```

執行後輸入 `test_data.csv` 即可測試。

---

## 注意事項

- `config.py` 內含敏感資訊，請勿上傳至公開平台（如 GitHub）
- 所有 LLM 回傳格式為 JSON，解析失敗時會印出原始內容供 debug
- Supervisor 每個步驟最多審查 3 輪，超過輪數會直接放行
