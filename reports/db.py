import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))


def query_df(sql: str):
    with snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        private_key_file=os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
        private_key_file_pwd=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE") or None,
        role="WALMART_TRANSFORMER",
        warehouse="WALMART_WH",
        database="WALMART_DB",
        schema=os.environ["WALMART_MARTS_SCHEMA"],
    ) as conn:
        df = conn.cursor().execute(sql).fetch_pandas_all()
    df.columns = df.columns.str.lower()
    return df