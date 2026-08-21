from google.adk.agents.llm_agent import Agent

from .database import (
    get_campaigns,
    get_content_item_by_id,
)


def get_planned_content_item(content_id: int) -> dict:
    """
    Retrieve a planned content item that needs social-media copy.

    Use this before generating content.
    """

    item = get_content_item_by_id(content_id)

    if item is None:
        return {
            "error": f"Content item {content_id} was not found."
        }

    return item


def get_campaign_for_content(campaign_id: int) -> dict:
    """
    Retrieve campaign information for a content item.

    Use campaign information to keep generated copy aligned
    with the campaign objective, audience, and platforms.
    """

    campaigns = get_campaigns()

    for campaign in campaigns:
        if campaign["campaign_id"] == campaign_id:
            return campaign

    return {
        "error": f"Campaign {campaign_id} was not found."
    }


content_generator = Agent(
    name="content_generator",
    model="gemini-3.5-flash-lite",
    description=(
        "Generates platform-specific social-media copy for approved "
        "planned content items."
    ),
    instruction="""
You are the Content Generation Agent for the AI Social Media Producer.

Your responsibility is to turn an approved planned content item
into draft social-media copy.

Before generating content:

1. Retrieve the content item using get_planned_content_item.
2. Retrieve its campaign using get_campaign_for_content.
3. Understand:
   - platform
   - content type
   - topic
   - content purpose
   - target audience
   - campaign objective
   - brand
   - campaign context

Only generate content for an existing content item.

The content item should normally have status "planned".

Your job is to write the actual social-media copy.

PLATFORM GUIDANCE:

Facebook:
- conversational;
- accessible;
- engaging;
- clear call to interaction where appropriate.

LinkedIn:
- professional;
- useful;
- credible;
- suitable for professional and career-focused audiences.

GROUNDING RULES:

Do not invent facts.

Do not invent:
- statistics;
- testimonials;
- learner results;
- courses;
- pricing;
- enrolment deadlines;
- certifications;
- partnerships;
- business achievements;
- product or service features not provided by the system.

Do not treat the topic or content purpose as proof that a factual
claim is true.

A planned topic describes what the content should discuss, not
verified evidence.

When the topic contains factual language such as:
- growing demand;
- market growth;
- high employment;
- industry trends;
- customer success;
- improved outcomes;

do not repeat those claims as established facts unless supporting
information has been provided by the campaign, brand data, or
another trusted source.

If evidence is unavailable, either:
1. write the content without making the factual claim; or
2. return a grounding warning explaining what evidence is required.

If the planned topic requires unsupported factual information,
say that additional brand information is required instead of
inventing the information.
""",
    tools=[
        get_planned_content_item,
        get_campaign_for_content,
    ],
)
