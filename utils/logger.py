from datetime import datetime


class Logger:
    def __init__(self):
        self.schema_findings = []
        self.cleaning_operations = []
        self.user_confirmations = []
        self.validation_results = []

    def log_schema(self, schema_result: dict):
        self.schema_findings.append({
            "timestamp": datetime.now().isoformat(),
            "result": schema_result
        })

    def log_cleaning(self, column: str, action: str, detail: str):
        self.cleaning_operations.append({
            "timestamp": datetime.now().isoformat(),
            "column": column,
            "action": action,
            "detail": detail
        })

    def log_user_input(self, column: str, issue: str, user_answer: str):
        self.user_confirmations.append({
            "timestamp": datetime.now().isoformat(),
            "column": column,
            "issue": issue,
            "user_answer": user_answer
        })

    def log_validation(self, validation_result: dict):
        self.validation_results.append({
            "timestamp": datetime.now().isoformat(),
            "result": validation_result
        })

    def print_report(self):
        print("\n" + "=" * 60)
        print("完整處理報告")
        print("=" * 60)

        print("\n[Schema Detection]")
        for entry in self.schema_findings:
            result = entry["result"]
            overall = result.get("overall_issues", [])
            print(f"  整體問題：{overall if overall else '無'}")
            for col in result.get("columns", []):
                issues = col.get("issues", [])
                print(f"  - {col['name']} ({col['detected_type']}): {issues if issues else '正常'}")

        print("\n[Data Cleaning]")
        if self.cleaning_operations:
            for op in self.cleaning_operations:
                print(f"  - [{op['column']}] {op['action']}: {op['detail']}")
        else:
            print("  無清理操作")

        print("\n[User Confirmations]")
        if self.user_confirmations:
            for uc in self.user_confirmations:
                print(f"  - [{uc['column']}] {uc['issue']} → 使用者選擇：{uc['user_answer']}")
        else:
            print("  無需使用者確認")

        print("\n[Validation]")
        for entry in self.validation_results:
            result = entry["result"]
            status = "通過" if result.get("passed") else "失敗"
            print(f"  結果：{status}")
            for check in result.get("checks", []):
                icon = "✓" if check.get("passed") else "✗"
                print(f"  {icon} {check['check_name']}: 預期 {check.get('expected')}，實際 {check.get('actual')}")
            if result.get("issues"):
                print(f"  問題：{result['issues']}")

        print("\n" + "=" * 60)
