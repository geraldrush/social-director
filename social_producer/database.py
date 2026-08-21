import os
from pathlib import Path

import clickhouse_connect
from dotenv import load_dotenv


# ---------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)


# ---------------------------------------------------------
# ClickHouse client
# ---------------------------------------------------------

client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.getenv("CLICKHOUSE_USER"),
    password=os.getenv("CLICKHOUSE_PASSWORD"),
    database=os.getenv("CLICKHOUSE_DATABASE"),
)


# =========================================================
# CONNECTION TEST
# =========================================================

def test_connection():
    """
    Test the ClickHouse connection.

    Returns the ClickHouse server version.
    """
    result = client.query("SELECT version()")
    return result.result_rows[0][0]


# =========================================================
# CAMPAIGNS
# =========================================================

def get_next_campaign_id():
    """
    Return the next campaign ID.

    For the current hackathon implementation we calculate
    the next ID using MAX(campaign_id) + 1.
    """
    result = client.query("""
        SELECT ifNull(max(campaign_id), 0) + 1
        FROM social_producer.campaigns
    """)

    return result.result_rows[0][0]


def create_campaign_record(
    campaign_id,
    brand_name,
    objective,
    target_audience,
    platforms,
    duration_days,
    status="draft",
):
    """
    Insert a campaign into ClickHouse.
    """

    client.insert(
        "social_producer.campaigns",
        [
            [
                campaign_id,
                brand_name,
                objective,
                target_audience,
                platforms,
                duration_days,
                status,
            ]
        ],
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

    return campaign_id


def get_campaigns():
    """
    Retrieve all campaigns from ClickHouse.
    """

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
        FROM social_producer.campaigns
        ORDER BY campaign_id
    """)

    campaigns = []

    for row in result.result_rows:
        campaigns.append(
            {
                "campaign_id": row[0],
                "brand_name": row[1],
                "objective": row[2],
                "target_audience": row[3],
                "platforms": row[4],
                "duration_days": row[5],
                "status": row[6],
                "created_at": row[7],
            }
        )

    return campaigns


# =========================================================
# CONTENT ITEMS
# =========================================================

def get_next_content_id():
    """
    Return the next content item ID.

    For the current implementation this uses
    MAX(content_id) + 1.
    """

    result = client.query("""
        SELECT ifNull(max(content_id), 0) + 1
        FROM social_producer.content_items
    """)

    return result.result_rows[0][0]


def create_content_item(
    content_id,
    campaign_id,
    platform,
    content_type,
    topic,
    content_text,
    status="draft",
    scheduled_at=None,
):
    """
    Insert a content item into ClickHouse.

    Each content item belongs to a campaign through campaign_id.
    """

    client.insert(
        "social_producer.content_items",
        [
            [
                content_id,
                campaign_id,
                platform,
                content_type,
                topic,
                content_text,
                status,
                scheduled_at,
            ]
        ],
        column_names=[
            "content_id",
            "campaign_id",
            "platform",
            "content_type",
            "topic",
            "content_text",
            "status",
            "scheduled_at",
        ],
    )

    return content_id


def get_content_items(campaign_id=None):
    """
    Retrieve content items.

    If campaign_id is supplied, return content belonging
    only to that campaign.

    Otherwise return all content items.
    """

    if campaign_id is not None:
        result = client.query(
            """
            SELECT
                content_id,
                campaign_id,
                platform,
                content_type,
                topic,
                content_text,
                status,
                scheduled_at,
                created_at
            FROM social_producer.content_items
            WHERE campaign_id = {campaign_id:UInt64}
            ORDER BY campaign_id, platform, content_id
            """,
            parameters={"campaign_id": campaign_id},
        )

    else:
        result = client.query("""
            SELECT
                content_id,
                campaign_id,
                platform,
                content_type,
                topic,
                content_text,
                status,
                scheduled_at,
                created_at
            FROM social_producer.content_items
            ORDER BY campaign_id, platform, content_id
        """)

    content_items = []

    for row in result.result_rows:
        content_items.append(
            {
                "content_id": row[0],
                "campaign_id": row[1],
                "platform": row[2],
                "content_type": row[3],
                "topic": row[4],
                "content_text": row[5],
                "status": row[6],
                "scheduled_at": row[7],
                "created_at": row[8],
            }
        )

    return content_items