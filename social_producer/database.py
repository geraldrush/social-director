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
    content_text="",
    status="planned",
    scheduled_at=None,
    campaign_day=None,
    content_purpose="",
):
    """
    Insert a content item into ClickHouse.

    Planned content can exist before final social-media copy
    has been generated.

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
                campaign_day,
                content_purpose,
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
            "campaign_day",
            "content_purpose",
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
                campaign_day,
                content_purpose,
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
                campaign_day,
                content_purpose,
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
                "campaign_day": row[5],
                "content_purpose": row[6],
                "content_text": row[7],
                "status": row[8],
                "scheduled_at": row[9],
                "created_at": row[10],
            }
        )

    return content_items


def get_content_item_by_id(content_id: int):
    """
    Retrieve one content item from ClickHouse by content ID.

    Returns None if the item does not exist.
    """

    result = client.query(
        """
        SELECT
            content_id,
            campaign_id,
            platform,
            content_type,
            topic,
            campaign_day,
            content_purpose,
            content_text,
            status,
            scheduled_at,
            created_at
        FROM social_producer.content_items
        WHERE content_id = {content_id:UInt64}
        LIMIT 1
        """,
        parameters={"content_id": content_id},
    )

    if not result.result_rows:
        return None

    row = result.result_rows[0]

    return {
        "content_id": row[0],
        "campaign_id": row[1],
        "platform": row[2],
        "content_type": row[3],
        "topic": row[4],
        "campaign_day": row[5],
        "content_purpose": row[6],
        "content_text": row[7],
        "status": row[8],
        "scheduled_at": row[9],
        "created_at": row[10],
    }


def save_generated_content(content_id: int, content_text: str):
    """
    Save generated social-media copy for an existing planned content item.

    The content item transitions from planned to draft.
    """

    existing_item = get_content_item_by_id(content_id)

    if existing_item is None:
        return {
            "saved": False,
            "error": f"Content item {content_id} was not found.",
        }

    client.command(
        """
        ALTER TABLE social_producer.content_items
        UPDATE
            content_text = {content_text:String},
            status = 'draft'
        WHERE content_id = {content_id:UInt64}
        """,
        parameters={
            "content_id": content_id,
            "content_text": content_text,
        },
    )

    return {
        "saved": True,
        "content_id": content_id,
        "status": "draft",
    }


# =========================================================
# AGENT EVENTS / OBSERVABILITY
# =========================================================

def get_next_agent_event_id():
    """
    Return the next agent event ID.

    For the current implementation this uses
    MAX(event_id) + 1.
    """

    result = client.query("""
        SELECT ifNull(max(event_id), 0) + 1
        FROM social_producer.agent_events
    """)

    return result.result_rows[0][0]


def log_agent_event(
    session_id,
    agent_name,
    event_type,
    parent_agent="",
    tool_name="",
    campaign_id=None,
    content_id=None,
    status="success",
    error_code="",
    model_name="",
    grounding_result="not_applicable",
    latency_ms=0,
    input_tokens=0,
    output_tokens=0,
    event_id=None,
):
    """
    Store one agent execution/observability event in ClickHouse.

    event_id is automatically generated when not explicitly supplied.

    This function currently supports manual and controlled event logging.
    Automatic ADK instrumentation will be added separately.
    """

    if event_id is None:
        event_id = get_next_agent_event_id()

    client.insert(
        "social_producer.agent_events",
        [
            [
                event_id,
                session_id,
                parent_agent,
                agent_name,
                event_type,
                tool_name,
                campaign_id,
                content_id,
                status,
                error_code,
                model_name,
                grounding_result,
                latency_ms,
                input_tokens,
                output_tokens,
            ]
        ],
        column_names=[
            "event_id",
            "session_id",
            "parent_agent",
            "agent_name",
            "event_type",
            "tool_name",
            "campaign_id",
            "content_id",
            "status",
            "error_code",
            "model_name",
            "grounding_result",
            "latency_ms",
            "input_tokens",
            "output_tokens",
        ],
    )

    return {
        "status": "success",
        "event_id": event_id,
    }


def get_agent_events(session_id=None):
    """
    Retrieve agent observability events.

    If session_id is provided, only events belonging to that
    workflow/session are returned.

    Otherwise all events are returned.
    """

    if session_id is not None:
        result = client.query(
            """
            SELECT
                event_id,
                session_id,
                parent_agent,
                agent_name,
                event_type,
                tool_name,
                campaign_id,
                content_id,
                status,
                error_code,
                model_name,
                grounding_result,
                latency_ms,
                input_tokens,
                output_tokens,
                created_at
            FROM social_producer.agent_events
            WHERE session_id = {session_id:String}
            ORDER BY created_at, event_id
            """,
            parameters={"session_id": session_id},
        )
    else:
        result = client.query("""
            SELECT
                event_id,
                session_id,
                parent_agent,
                agent_name,
                event_type,
                tool_name,
                campaign_id,
                content_id,
                status,
                error_code,
                model_name,
                grounding_result,
                latency_ms,
                input_tokens,
                output_tokens,
                created_at
            FROM social_producer.agent_events
            ORDER BY created_at, event_id
        """)

    events = []

    for row in result.result_rows:
        events.append(
            {
                "event_id": row[0],
                "session_id": row[1],
                "parent_agent": row[2],
                "agent_name": row[3],
                "event_type": row[4],
                "tool_name": row[5],
                "campaign_id": row[6],
                "content_id": row[7],
                "status": row[8],
                "error_code": row[9],
                "model_name": row[10],
                "grounding_result": row[11],
                "latency_ms": row[12],
                "input_tokens": row[13],
                "output_tokens": row[14],
                "created_at": row[15],
            }
        )

    return events