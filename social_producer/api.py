from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


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


@app.get("/content/{content_id}")
def content_item(content_id: int):
    item = get_content_item_by_id(content_id)

    if item is None:
        return {
            "error": f"Content item {content_id} was not found."
        }

    return item


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
        parameters={"recommendation_id": recommendation_id},
    )

    if not result.result_rows:
        return {
            "error": f"Recommendation {recommendation_id} was not found."
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
            "experiment_result_id": experiment_result_id
        },
    )

    if not result.result_rows:
        return {
            "error": (
                f"Experiment result {experiment_result_id} "
                "was not found."
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