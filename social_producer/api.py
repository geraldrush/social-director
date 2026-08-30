import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .clickhouse_mcp import clickhouse_mcp
from .database import (
    client,
    get_campaigns,
    get_campaign_facts,
    get_campaign_performance,
    get_platform_performance,
    get_content_item_by_id,
)


app = FastAPI(
    title="Premiere API",
    version="0.3.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# =========================================================
# ADK RUNTIME
# =========================================================

agent_session_service = InMemorySessionService()


campaign_analysis_agent = Agent(
    name="premiere_campaign_analyst",
    model="gemini-3.5-flash",
    description=(
        "Read-only Premiere campaign analytics agent "
        "powered by ClickHouse MCP."
    ),
    instruction="""
You are Premiere's campaign analytics agent.

Your role is to analyse film release campaign performance using
ClickHouse.

IMPORTANT DATA ACCESS RULE:

You MUST retrieve campaign and performance information using the
official mcp-clickhouse MCP tools.

Available ClickHouse MCP capabilities include:

- list_databases
- list_tables
- run_query

For campaign analysis, you MUST use run_query.

Do not use remembered campaign values.
Do not rely on stored assumptions.
Do not invent metrics.
Do not modify data.

Use only evidence returned from ClickHouse during the current run.

When asked to analyse a campaign:

1. Query the relevant campaign.
2. Query platform performance.
3. Calculate engagement rate.
4. Calculate click-through rate.
5. Compare platforms.
6. Identify evidence-backed optimisation opportunities.
7. Explain the figures supporting the conclusion.
8. Clearly state when the dataset represents simulated
   development telemetry rather than real-world campaign
   performance.

Engagement rate should be calculated as:

(likes + comments + shares + saves) / impressions * 100

CTR should be calculated as:

clicks / impressions * 100

The ClickHouse connection is strictly read-only.
""",
    tools=[
        clickhouse_mcp,
    ],
)


agent_runner = Runner(
    app_name="premiere",
    agent=campaign_analysis_agent,
    session_service=agent_session_service,
)


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Premiere API",
        "agent_runtime": "Google ADK",
        "model": "gemini-3.5-flash",
        "backend": "Vertex AI",
        "mcp": "mcp-clickhouse",
        "database": "ClickHouse Cloud",
    }


# =========================================================
# CAMPAIGNS
# =========================================================

@app.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int):
    campaigns = get_campaigns()

    for campaign in campaigns:
        if campaign["campaign_id"] == campaign_id:
            return campaign

    return {
        "error": f"Campaign {campaign_id} was not found."
    }


@app.get("/campaigns/{campaign_id}/facts")
def campaign_facts(campaign_id: int):
    return get_campaign_facts(campaign_id)


@app.get("/campaigns/{campaign_id}/performance")
def campaign_performance(campaign_id: int):
    return get_campaign_performance(campaign_id)


@app.get("/campaigns/{campaign_id}/platforms")
def platform_performance(campaign_id: int):
    return get_platform_performance(campaign_id)


# =========================================================
# CONTENT
# =========================================================

@app.get("/content/{content_id}")
def content_item(content_id: int):
    item = get_content_item_by_id(content_id)

    if item is None:
        return {
            "error": f"Content item {content_id} was not found."
        }

    return item


# =========================================================
# OPTIMISATION RECOMMENDATIONS
# =========================================================

@app.get("/recommendations/{recommendation_id}")
def get_recommendation(recommendation_id: int):
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
            experiment_content_id,
            success_metric,
            status,
            created_at
        FROM optimisation_recommendations
        WHERE recommendation_id = %(recommendation_id)s
        LIMIT 1
        """,
        parameters={
            "recommendation_id": recommendation_id,
        },
    )

    if not result.result_rows:
        return {
            "error": (
                f"Recommendation {recommendation_id} "
                "was not found."
            )
        }

    row = result.result_rows[0]

    return {
        "recommendation_id": row[0],
        "campaign_id": row[1],
        "recommendation_type": row[2],
        "observation": row[3],
        "hypothesis": row[4],
        "recommendation": row[5],
        "experiment": row[6],
        "experiment_content_id": row[7],
        "success_metric": row[8],
        "status": row[9],
        "created_at": row[10],
    }


# =========================================================
# EXPERIMENT RESULTS
# =========================================================

@app.get("/experiment-results/{experiment_result_id}")
def get_experiment_result(experiment_result_id: int):
    result = client.query(
        """
        SELECT
            experiment_result_id,
            recommendation_id,
            campaign_id,
            content_id,
            platform,
            baseline_ctr,
            experiment_ctr,
            ctr_change_pp,
            ctr_relative_change_pct,
            baseline_engagement_rate,
            experiment_engagement_rate,
            engagement_change_pp,
            success,
            outcome,
            decision,
            data_source,
            evaluated_at
        FROM experiment_results
        WHERE experiment_result_id = %(experiment_result_id)s
        LIMIT 1
        """,
        parameters={
            "experiment_result_id": experiment_result_id,
        },
    )

    if not result.result_rows:
        return {
            "error": (
                f"Experiment result "
                f"{experiment_result_id} was not found."
            )
        }

    row = result.result_rows[0]

    return {
        "experiment_result_id": row[0],
        "recommendation_id": row[1],
        "campaign_id": row[2],
        "content_id": row[3],
        "platform": row[4],
        "baseline_ctr": row[5],
        "experiment_ctr": row[6],
        "ctr_change_pp": row[7],
        "ctr_relative_change_pct": row[8],
        "baseline_engagement_rate": row[9],
        "experiment_engagement_rate": row[10],
        "engagement_change_pp": row[11],
        "success": bool(row[12]),
        "outcome": row[13],
        "decision": row[14],
        "data_source": row[15],
        "evaluated_at": row[16],
    }


# =========================================================
# LIVE MCP CAMPAIGN ANALYSIS
# =========================================================

@app.post("/agent/analyse-campaign/{campaign_id}")
async def analyse_campaign_with_agent(campaign_id: int):
    """
    Run a dedicated Premiere campaign analyst.

    This endpoint intentionally uses an MCP-only ADK agent for
    analytical campaign reads.

    The agent does not have access to Premiere's direct Python
    database tools.
    """

    user_id = "premiere-ui"

    session_id = (
        f"campaign-{campaign_id}-"
        f"{uuid.uuid4().hex[:8]}"
    )

    await agent_session_service.create_session(
        app_name="premiere",
        user_id=user_id,
        session_id=session_id,
    )

    prompt = f"""
Analyse Campaign {campaign_id}.

You MUST query ClickHouse using the official mcp-clickhouse
run_query tool before answering.

Retrieve the campaign's current performance data from ClickHouse.

Determine:

1. Which platform currently has the highest engagement rate?
2. Which platform currently has the highest click-through rate?
3. What important optimisation opportunity is visible in the
   performance data?

For each conclusion:

- show the figures used;
- explain how the metric was calculated;
- base the answer only on data retrieved in this run.

Use engagement rate:

(likes + comments + shares + saves) / impressions * 100

Use CTR:

clicks / impressions * 100

Do not modify any data.

Do not rely on remembered campaign values.

Where relevant, make clear that this dataset represents simulated
development campaign telemetry and should not be interpreted as
real-world social-media performance.
"""

    final_response = ""
    tools_used: list[str] = []

    async for event in agent_runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=prompt,
                )
            ],
        ),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                function_call = getattr(
                    part,
                    "function_call",
                    None,
                )

                if function_call:
                    tools_used.append(
                        function_call.name
                    )

        if event.is_final_response():
            if (
                event.content
                and event.content.parts
            ):
                final_response = "".join(
                    part.text or ""
                    for part in event.content.parts
                    if getattr(
                        part,
                        "text",
                        None,
                    )
                )

    unique_tools = list(
        dict.fromkeys(tools_used)
    )

    mcp_verified = (
        "run_query" in unique_tools
    )

    return {
        "campaign_id": campaign_id,
        "analysis": final_response,
        "tools_used": unique_tools,
        "mcp_verified": mcp_verified,
        "runtime": {
            "model": "gemini-3.5-flash",
            "backend": "Vertex AI",
            "agent_framework": "Google ADK",
            "agent": "premiere_campaign_analyst",
            "mcp": "mcp-clickhouse",
            "database": "ClickHouse Cloud",
            "database_access": "read-only",
        },
    }