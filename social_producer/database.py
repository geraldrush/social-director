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

def get_tool_analytics():
    """
    Return aggregated tool usage and performance analytics
    from ClickHouse agent_events.
    """

    result = client.query("""
        SELECT
            tool_name,
            count() AS calls,
            countIf(status = 'success') AS successes,
            countIf(status != 'success') AS failures,
            round(avg(latency_ms), 2) AS avg_latency_ms,
            max(latency_ms) AS max_latency_ms
        FROM social_producer.agent_events
        WHERE event_type = 'tool_call'
        GROUP BY tool_name
        ORDER BY calls DESC
    """)

    analytics = []

    for row in result.result_rows:
        analytics.append({
            "tool_name": row[0],
            "calls": row[1],
            "successes": row[2],
            "failures": row[3],
            "avg_latency_ms": row[4],
            "max_latency_ms": row[5],
        })

    return analytics


def get_session_analytics():
    """
    Return aggregated agent/tool activity grouped by session.
    """

    result = client.query("""
        SELECT
            session_id,
            count() AS event_count,
            countIf(event_type = 'tool_call') AS tool_calls,
            countIf(status = 'success') AS successes,
            countIf(status != 'success') AS failures,
            round(avg(latency_ms), 2) AS avg_latency_ms,
            sum(latency_ms) AS total_latency_ms,
            min(created_at) AS started_at,
            max(created_at) AS ended_at
        FROM social_producer.agent_events
        GROUP BY session_id
        ORDER BY started_at DESC
    """)

    sessions = []

    for row in result.result_rows:
        sessions.append({
            "session_id": row[0],
            "event_count": row[1],
            "tool_calls": row[2],
            "successes": row[3],
            "failures": row[4],
            "avg_latency_ms": row[5],
            "total_latency_ms": row[6],
            "started_at": row[7],
            "ended_at": row[8],
        })

    return sessions

def get_campaign_performance(campaign_id: int):
    """
    Return aggregated performance for each content item
    belonging to a campaign.
    """

    result = client.query(
        """
        SELECT
            p.content_id,
            p.platform,
            c.content_type,
            c.topic,
            sum(p.impressions) AS impressions,
            sum(p.views) AS views,
            sum(p.likes) AS likes,
            sum(p.comments) AS comments,
            sum(p.shares) AS shares,
            sum(p.saves) AS saves,
            sum(p.clicks) AS clicks
        FROM social_producer.content_performance_daily AS p
        LEFT JOIN social_producer.content_items AS c
            ON p.content_id = c.content_id
           AND p.campaign_id = c.campaign_id
        WHERE p.campaign_id = {campaign_id:UInt64}
        GROUP BY
            p.content_id,
            p.platform,
            c.content_type,
            c.topic
        ORDER BY impressions DESC
        """,
        parameters={"campaign_id": campaign_id},
    )

    columns = [
        "content_id",
        "platform",
        "content_type",
        "topic",
        "impressions",
        "views",
        "likes",
        "comments",
        "shares",
        "saves",
        "clicks",
    ]

    return [
        dict(zip(columns, row))
        for row in result.result_rows
    ]


def get_platform_performance(campaign_id: int):
    """
    Aggregate campaign engagement by social platform.
    """

    result = client.query(
        """
        SELECT
            platform,
            impressions,
            views,
            likes,
            comments,
            shares,
            saves,
            clicks,
            round(
                100.0 * (likes + comments + shares + saves)
                / nullIf(impressions, 0),
                2
            ) AS engagement_rate,
            round(
                100.0 * clicks
                / nullIf(impressions, 0),
                2
            ) AS click_rate
        FROM
        (
            SELECT
                platform,
                sum(impressions) AS impressions,
                sum(views) AS views,
                sum(likes) AS likes,
                sum(comments) AS comments,
                sum(shares) AS shares,
                sum(saves) AS saves,
                sum(clicks) AS clicks
            FROM social_producer.content_performance_daily
            WHERE campaign_id = {campaign_id:UInt64}
            GROUP BY platform
        )
        ORDER BY impressions DESC
        """,
        parameters={"campaign_id": campaign_id},
    )

    columns = [
        "platform",
        "impressions",
        "views",
        "likes",
        "comments",
        "shares",
        "saves",
        "clicks",
        "engagement_rate",
        "click_rate",
    ]

    return [
        dict(zip(columns, row))
        for row in result.result_rows
    ]

def get_next_recommendation_id():
    """
    Return the next available optimisation recommendation ID.
    """
    result = client.query("""
        SELECT ifNull(max(recommendation_id), 0) + 1
        FROM social_producer.optimisation_recommendations
    """)

    return result.result_rows[0][0]


def save_optimisation_recommendation(
    campaign_id: int,
    recommendation_type: str,
    observation: str,
    hypothesis: str,
    recommendation: str,
    experiment: str,
    success_metric: str,
):
    """
    Save a proposed optimisation recommendation to ClickHouse.

    Recommendations are always created with status='proposed'.
    Human approval is required before they can influence planning.
    """

    recommendation_id = get_next_recommendation_id()

    client.insert(
        "social_producer.optimisation_recommendations",
        [[
            recommendation_id,
            campaign_id,
            recommendation_type,
            observation,
            hypothesis,
            recommendation,
            experiment,
            success_metric,
            "proposed",
        ]],
        column_names=[
            "recommendation_id",
            "campaign_id",
            "recommendation_type",
            "observation",
            "hypothesis",
            "recommendation",
            "experiment",
            "success_metric",
            "status",
        ],
    )

    return {
        "status": "success",
        "recommendation_id": recommendation_id,
        "campaign_id": campaign_id,
        "recommendation_status": "proposed",
    }


def get_optimisation_recommendations(
    campaign_id: int,
    status: str | None = None,
):
    """
    Return optimisation recommendations for a campaign.

    Optionally filter by recommendation status.
    """

    if status:
        result = client.query(
            """
            SELECT
                recommendation_id,
                campaign_id,
                recommendation_type,
                observation,
                hypothesis,
                recommendation,
                experiment,
                success_metric,
                status,
                created_at
            FROM social_producer.optimisation_recommendations
            WHERE campaign_id = {campaign_id:UInt64}
              AND status = {status:String}
            ORDER BY created_at DESC, recommendation_id DESC
            """,
            parameters={
                "campaign_id": campaign_id,
                "status": status,
            },
        )
    else:
        result = client.query(
            """
            SELECT
                recommendation_id,
                campaign_id,
                recommendation_type,
                observation,
                hypothesis,
                recommendation,
                experiment,
                success_metric,
                status,
                created_at
            FROM social_producer.optimisation_recommendations
            WHERE campaign_id = {campaign_id:UInt64}
            ORDER BY created_at DESC, recommendation_id DESC
            """,
            parameters={
                "campaign_id": campaign_id,
            },
        )

    recommendations = []

    for row in result.result_rows:
        recommendations.append({
            "recommendation_id": row[0],
            "campaign_id": row[1],
            "recommendation_type": row[2],
            "observation": row[3],
            "hypothesis": row[4],
            "recommendation": row[5],
            "experiment": row[6],
            "success_metric": row[7],
            "status": row[8],
            "created_at": row[9],
        })

    return recommendations


def approve_optimisation_recommendation(
    recommendation_id: int,
):
    """
    Approve a proposed optimisation recommendation.

    ClickHouse mutations are used deliberately here because approval
    is a low-frequency human workflow rather than a high-volume event.
    """

    existing = client.query(
        """
        SELECT
            recommendation_id,
            campaign_id,
            status
        FROM social_producer.optimisation_recommendations
        WHERE recommendation_id = {recommendation_id:UInt64}
        LIMIT 1
        """,
        parameters={
            "recommendation_id": recommendation_id,
        },
    )

    if not existing.result_rows:
        return {
            "status": "error",
            "message": "Recommendation not found.",
        }

    row = existing.result_rows[0]
    campaign_id = row[1]
    current_status = row[2]

    if current_status != "proposed":
        return {
            "status": "error",
            "recommendation_id": recommendation_id,
            "current_status": current_status,
            "message": (
                "Only proposed recommendations can be approved."
            ),
        }

    client.command(
        """
        ALTER TABLE social_producer.optimisation_recommendations
        UPDATE status = 'approved'
        WHERE recommendation_id = {recommendation_id:UInt64}
        """,
        parameters={
            "recommendation_id": recommendation_id,
        },
    )

    return {
        "status": "success",
        "recommendation_id": recommendation_id,
        "campaign_id": campaign_id,
        "recommendation_status": "approved",
    }