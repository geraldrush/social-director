import os
from pathlib import Path

import clickhouse_connect
from dotenv import load_dotenv


env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)


client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.getenv("CLICKHOUSE_USER"),
    password=os.getenv("CLICKHOUSE_PASSWORD"),
    database=os.getenv("CLICKHOUSE_DATABASE"),
)


def test_connection():
    result = client.query("SELECT version()")
    return result.result_rows[0][0]


def get_next_campaign_id() -> int:
    result = client.query("""
        SELECT coalesce(max(campaign_id), 0) + 1
        FROM campaigns
    """)

    return result.result_rows[0][0]


def create_campaign_record(
    campaign_id: int,
    brand_name: str,
    objective: str,
    target_audience: str,
    platforms: list[str],
    duration_days: int,
    status: str = "draft",
) -> None:

    client.insert(
        "campaigns",
        [[
            campaign_id,
            brand_name,
            objective,
            target_audience,
            platforms,
            duration_days,
            status,
        ]],
        column_names=[
            "campaign_id",
            "brand_name",
            "objective",
            "target_audience",
            "platforms",
            "duration_days",
            "status",
        ],
    )


def get_campaigns() -> list[dict]:
    result = client.query("""
        SELECT
            campaign_id,
            brand_name,
            objective,
            target_audience,
            platforms,
            duration_days,
            status,
            created_at
        FROM campaigns
        ORDER BY campaign_id
    """)

    campaigns = []

    for row in result.result_rows:
        campaigns.append({
            "campaign_id": row[0],
            "brand_name": row[1],
            "objective": row[2],
            "target_audience": row[3],
            "platforms": row[4],
            "duration_days": row[5],
            "status": row[6],
            "created_at": str(row[7]),
        })

    return campaigns