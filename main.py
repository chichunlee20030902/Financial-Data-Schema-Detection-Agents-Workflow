import json
import config
from utils.file_loader import load
from utils.db_connector import DBConnector
from utils.logger import Logger
from agents.supervisor import SupervisorAgent
from agents.schema_detector import SchemaDetectorAgent
from agents.data_cleaner import DataCleanerAgent
from agents.sql_writer import SQLWriterAgent
from agents.validator import ValidatorAgent


def supervised_step(supervisor, agent, agent_name, agent_output, max_rounds=None):
    if max_rounds is None:
        max_rounds = config.MAX_REVIEW_ROUNDS

    for round_num in range(max_rounds):
        review = supervisor.review(agent_name, json.dumps(agent_output, ensure_ascii=False))
        if review.get("approved"):
            print(f"[Supervisor] {agent_name} 審查通過：{review.get('summary', '')}")
            return agent_output
        else:
            feedback = review.get("feedback", "")
            print(f"[Supervisor] {agent_name} 需要修改（第 {round_num + 1} 輪）：{feedback}")
            agent_output = agent.revise(feedback)

    print(f"[Supervisor] {agent_name} 已達最大審查輪數，直接放行")
    return agent_output


def main():
    file_path = input("請輸入檔案路徑（CSV 或 Excel）：").strip()

    # 載入資料
    print("\n正在載入檔案...")
    df = load(file_path)
    print(f"載入成功：{len(df)} 行，{len(df.columns)} 欄")

    # 初始化
    logger = Logger()
    supervisor = SupervisorAgent()
    schema_detector = SchemaDetectorAgent()
    data_cleaner = DataCleanerAgent()
    sql_writer = SQLWriterAgent()
    validator = ValidatorAgent()
    db = DBConnector()

    # Step 1: Schema Detection
    print("\n--- Step 1: Schema Detection ---")
    schema_result = schema_detector.detect(df)
    schema_result = supervised_step(supervisor, schema_detector, "SchemaDetector", schema_result)
    logger.log_schema(schema_result)

    if not schema_result.get("can_proceed", True):
        print("[main] Schema 檢測發現無法繼續的問題，流程中止")
        logger.print_report()
        return

    # Step 2: Data Cleaning
    print("\n--- Step 2: Data Cleaning ---")
    cleaning_plan = data_cleaner.plan(schema_result, df.head(20))
    cleaning_plan = supervised_step(supervisor, data_cleaner, "DataCleaner", cleaning_plan)

    # 處理需要使用者確認的項目
    for item in cleaning_plan.get("requires_user_input", []):
        print(f"\n[需要確認] 欄位 '{item['column']}'：{item['issue']}")
        for i, opt in enumerate(item.get("options", []), 1):
            print(f"  {i}. {opt}")
        answer = input("請輸入選項編號或自訂處理方式：").strip()
        logger.log_user_input(item["column"], item["issue"], answer)

    cleaned_df = data_cleaner.execute(df, cleaning_plan)

    for step in cleaning_plan.get("cleaning_plan", []):
        if step.get("auto_fixable"):
            logger.log_cleaning(step["column"], step["action"], step["detail"])

    # Step 3: SQL Writing
    print("\n--- Step 3: SQL Writing ---")
    sql_result = sql_writer.generate(schema_result)
    sql_result = supervised_step(supervisor, sql_writer, "SQLWriter", sql_result)

    db.connect()
    db.create_table(sql_result["create_table_sql"])
    db.insert_dataframe(cleaned_df, sql_result["table_name"], sql_result["column_mapping"])

    # Step 4: Validation
    print("\n--- Step 4: Validation ---")
    validation_result = validator.validate(cleaned_df, sql_result["table_name"], db)
    validation_result = supervised_step(supervisor, validator, "Validator", validation_result)
    logger.log_validation(validation_result)

    if not validation_result.get("passed"):
        print("[main] 驗證未通過，請人工處理以下問題：")
        for issue in validation_result.get("issues", []):
            print(f"  - {issue}")

    db.close()

    # 最終報告
    logger.print_report()


if __name__ == "__main__":
    main()
