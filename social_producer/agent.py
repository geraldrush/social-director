from google.adk.agents.llm_agent import Agent

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
                "IT training"
            ]
        }
    }

    brand = brands.get(brand_name.lower())

    if brand:
        return brand

    return {
        "error": f"No information found for {brand_name}"
    }

campaigns = []

def create_campaign(
    brand_name: str,
    objective: str,
    target_audience: str,
    platforms: list[str],
    duration_days: int
) -> dict:
    """Create a new social media campaign."""

    campaign = {
        "id": len(campaigns) + 1,
        "brand_name": brand_name,
        "objective": objective,
        "target_audience": target_audience,
        "platforms": platforms,
        "duration_days": duration_days,
        "status": "draft"
    }

    campaigns.append(campaign)

    return {
        "status": "success",
        "message": "Campaign created successfully.",
        "campaign": campaign
    }

root_agent = Agent(
    model='gemini-3.5-flash',
    name='social_media_producer',
    

    description=(
        'An AI social media producer that helps businesses plan '
        'and create social media campaigns.'
    ),

    instruction="""
You are an AI Social Media Producer.

Your job is to help businesses plan and produce effective
social media campaigns.

When a user gives you a campaign brief:

1. Understand the business or brand.
2. Identify the campaign objective.
3. Identify the target audience.
4. Recommend suitable social media platforms.
5. Develop appropriate content ideas.
6. Create platform-specific social media copy.
7. Suggest a call to action.

Do not assume information that the user has not provided.
Ask for important missing information when necessary.

For now, you only PLAN and CREATE content.
You do not publish or schedule posts.

When enough campaign information has been collected, summarise
the proposed campaign and ask the user for confirmation before
creating it.

Only call the create_campaign tool after the user clearly
confirms that they want the campaign created.

New campaigns must remain in draft status.
""",
tools=[
    get_brand_details,
    create_campaign,
],
)