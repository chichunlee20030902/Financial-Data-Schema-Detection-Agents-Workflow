import mysql.connector
import pandas as pd
import config


class DBConnector:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = mysql.connector.connect(**config.DB_CONFIG)
        self.cursor = self.conn.cursor(dictionary=True)
        print("[DBConnector] 資料庫連線成功")

    def create_table(self, create_sql: str):
        self.cursor.execute(create_sql)
        self.conn.commit()
        print("[DBConnector] 資料表建立成功")

    def insert_dataframe(self, df: pd.DataFrame, table_name: str, column_mapping: dict):
        df_renamed = df.rename(columns=column_mapping)
        cols = list(df_renamed.columns)
        placeholders = ", ".join(["%s"] * len(cols))
        col_names = ", ".join([f"`{c}`" for c in cols])
        sql = f"INSERT INTO `{table_name}` ({col_names}) VALUES ({placeholders})"

        rows = [tuple(row) for row in df_renamed.itertuples(index=False, name=None)]
        self.cursor.executemany(sql, rows)
        self.conn.commit()
        print(f"[DBConnector] 成功寫入 {len(rows)} 筆資料到 {table_name}")

    def query(self, sql: str) -> list:
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("[DBConnector] 資料庫連線已關閉")
