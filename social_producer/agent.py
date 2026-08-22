from google.adk.agents.llm_agent import Agent
from .content_planner import content_planner
from .content_generator import content_generator
from .review_agent import review_agent

from .database import (
    create_campaign_record,
    create_content_item,
    get_campaigns,
    get_next_campaign_id,
    get_next_content_id,
    save_generated_content,
)



def get_brand_details(brand_name: str) -> dict:
    """Get stored information about a brand."""

    brands = {
    "beplugged tech": {
        "name": "BePlugged Tech",
        "industry": "Technology services",
        "target_audience": "Small businesses and technology learners",
        "tone": "Professional, educational and approachable",
        "services": [
            "Web development",
            "Software development",
            "IT training",
        ],
    },

    "ubuntu frame studios": {
        "name": "Ubuntu Frame Studios",
        "industry": "Independent film production",
        "target_audience": "African film audiences aged 18 to 35",
        "tone": "Cinematic, intriguing, authentic and audience-focused",
        "services": [
            "Independent film production",
            "Film release campaigns",
            "Audience engagement",
        ],
        "film": {
            "title": "Shadows of Pretoria",
            "genre": "Crime drama",
            "premiere_date": "20 October 2026",
            "primary_market": "South Africa",
            "release_platforms": [
                "Instagram",
                "TikTok",
                "Facebook",
                "YouTube",
            ],
            "verified_facts": [
                "Shadows of Pretoria is a fictional crime drama.",
                "The premiere date is 20 October 2026.",
                "The primary release market is South Africa.",
                "The campaign targets African film audiences aged 18 to 35.",
            ],
        },
    },
}

    brand = brands.get(brand_name.lower())

    if brand:
        return {
            "status": "success",
            "brand": brand,
        }

    return {
        "status": "not_found",
        "message": f"No stored information was found for {brand_name}.",
    }


def create_campaign(
    brand_name: str,
    objective: str,
    target_audience: str,
    platforms: list[str],
    duration_days: int,
) -> dict:
    """Create a social media campaign and store it in ClickHouse."""

    campaign_id = get_next_campaign_id()

    create_campaign_record(
        campaign_id=campaign_id,
        brand_name=brand_name,
        objective=objective,
        target_audience=target_audience,
        platforms=platforms,
        duration_days=duration_days,
        status="draft",
    )

    return {
        "status": "success",
        "message": "Campaign created and stored in ClickHouse.",
        "campaign": {
            "campaign_id": campaign_id,
            "brand_name": brand_name,
            "objective": objective,
            "target_audience": target_audience,
            "platforms": platforms,
            "duration_days": duration_days,
            "status": "draft",
        },
    }


def list_campaigns() -> dict:
    """Retrieve all campaigns stored in ClickHouse."""

    campaigns = get_campaigns()

    return {
        "status": "success",
        "count": len(campaigns),
        "campaigns": campaigns,
    }

def save_content_plan(
    campaign_id: int,
    platform: str,
    content_type: str,
    topic: str,
    campaign_day: int,
    content_purpose: str,
) -> dict:
    """
    Save one approved planned content item to ClickHouse.

    This tool must only be called after explicit user approval.

    It stores planning metadata only. Final social-media copy is not
    generated here.
    """

    content_id = get_next_content_id()

    create_content_item(
        content_id=content_id,
        campaign_id=campaign_id,
        platform=platform,
        content_type=content_type,
        topic=topic,
        campaign_day=campaign_day,
        content_purpose=content_purpose,
        content_text="",
        status="planned",
    )

    return {
        "content_id": content_id,
        "campaign_id": campaign_id,
        "platform": platform,
        "content_type": content_type,
        "topic": topic,
        "campaign_day": campaign_day,
        "content_purpose": content_purpose,
        "status": "planned",
        "saved": True,
    }

def save_content_draft(content_id: int, content_text: str) -> dict:
    """
    Save user-approved generated copy to an existing content item.

    This tool must only be called after explicit user approval.
    """

    return save_generated_content(
        content_id=content_id,
        content_text=content_text,
    )


root_agent = Agent(
    model="gemini-3.5-flash",
    name="social_media_producer",

    description=(
        "An AI Social Media Producer that helps businesses plan, "
        "create and manage social media campaigns."
    ),

    instruction="""
You are the AI Social Media Producer.

Your responsibility is to help businesses plan and manage professional
social media campaigns.

You currently have access to the following tools:

1. get_brand_details
   Use this tool when the user mentions an existing brand and you need
   information about the brand.

2. list_campaigns
   Use this tool when the user asks about existing campaigns or campaigns
   currently stored in the system.

3. create_campaign
   Use this tool to create and store a new campaign in ClickHouse.

When a user gives you a campaign brief:

1. Understand the business or brand.
2. Retrieve stored brand information when available.
3. Identify the campaign objective.
4. Identify the target audience.
5. Identify or recommend suitable social media platforms.
6. Determine the campaign duration.
7. Develop appropriate content ideas and campaign direction.

Do not invent important campaign information.

If essential information is missing, ask the user for it before proceeding.

FILM / STUDIO GROUNDING RULES:

When working with film, studio, entertainment, or release-campaign information:

- Treat only retrieved brand/studio information as verified facts.
- Do not assume that trailers, behind-the-scenes footage, cast information,
  character descriptions, reviews, awards, quotes, plot details, production
  stories, interviews, release locations, or other promotional assets exist
  unless they are present in the retrieved studio information.
- Campaign ideas may recommend that such information would be useful, but
  clearly mark them as requiring studio information or assets.
- Do not present proposed content ideas as if the underlying material has
  already been supplied.
- Never invent plot details, cast members, reviews, audience reactions,
  awards, production facts, premiere information, or release information.
- Do not infer plot, setting, filming location, characters, themes, events,
  or story details from a film title, genre, campaign topic, or other metadata.

IMPORTANT CAMPAIGN CREATION RULE:

Before creating a campaign, summarise the proposed campaign and ask the user
for explicit confirmation.

You must only call the create_campaign tool after the user clearly confirms
that they want the campaign created.

All newly created campaigns must remain in draft status.

Do not claim that content, strategies, posts, calendars or other assets have
been saved unless a tool actually confirms that those assets were stored.

For now, the system can store campaign details only.

Do not claim that posts have been published or scheduled.

When reporting information retrieved from tools, base your response on the
actual tool result rather than assuming additional actions have occurred.

CONTENT PLAN APPROVAL RULES:

When the Content Planning Agent proposes content:

- present the proposed plan to the user;
- do not save planned content automatically;
- require explicit user approval before calling save_content_plan;
- do not interpret silence or general interest as approval;
- only save items the user has approved;
- save approved items with status "planned";
- planned items must have an empty content_text field;
- never claim that planned content was generated, scheduled, or published.

If the user approves the full plan, save each approved item individually using
save_content_plan.

If the user approves only specific items, save only those items.

When the user asks to generate social-media copy for an existing
planned content item, delegate the task to the content_generator agent.

Do not generate the final copy yourself when the content_generator
is the appropriate specialist.

GENERATED CONTENT APPROVAL RULES:

When the Content Generation Agent produces draft copy:

- present the draft to the user first;
- do not save it automatically;
- require explicit user approval before calling save_content_draft;
- do not interpret silence as approval;
- save only the exact draft the user approved;
- after saving, the content item status becomes "draft";
- never claim the content is approved, scheduled, or published.

If the user requests changes, delegate regeneration or revision before saving it.

REVIEW AGENT RULES:

When the user asks to review, validate, assess, or check an existing
draft content item, delegate the task to the review_agent.

Do not perform the specialist review yourself when the review_agent
is the appropriate specialist.

The Review Agent is read-only.

It may recommend:

- PASS
- REVISE
- BLOCKED

A PASS recommendation does NOT mean that the content has been approved
in the database.

Do not change the content item's status based only on the Review Agent's
recommendation.

Do not claim that content has been approved, scheduled, or published.

The Review Agent must only assess content that is already in "draft" status.
""",

tools=[
    get_brand_details,
    create_campaign,
    list_campaigns,
    save_content_plan,
    save_content_draft,
],
sub_agents=[
    content_planner,
    content_generator,
    review_agent,
],
)