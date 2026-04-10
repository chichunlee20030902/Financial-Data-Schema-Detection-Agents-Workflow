import pandas as pd


def load(file_path: str) -> pd.DataFrame:
    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)
    elif file_path.endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"不支援的檔案格式：{file_path}")


def get_schema_info(df: pd.DataFrame) -> str:
    lines = [
        f"總行數：{len(df)}",
        f"總欄數：{len(df.columns)}",
        ""
    ]

    for col in df.columns:
        sample_values = df[col].dropna().head(3).tolist()
        missing_count = df[col].isna().sum()
        dtype = str(df[col].dtype)

        lines.append(f"欄位名稱：{col}")
        lines.append(f"  型別：{dtype}")
        lines.append(f"  樣本值：{sample_values}")
        lines.append(f"  缺失值數量：{missing_count}")
        lines.append("")

    return "\n".join(lines)
