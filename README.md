# AI Social Media Producer

## Project Overview

AI Social Media Producer is an agentic application being developed for the
Agentic Cinema Hackathon.

The project aims to automate parts of the social media campaign workflow,
including campaign planning, content creation, review, analytics and
campaign optimisation.

## Current Architecture

The project currently uses:

- Google Agent Development Kit (ADK)
- Gemini
- Python

ClickHouse will be used as the main data and analytics platform.

## Development Progress

### Phase 1 - Initial Agent

The first version of the project contains one root agent called
`social_media_producer`.

The agent can:

- understand a social media campaign request;
- request missing campaign information;
- retrieve stored brand information using a tool;
- prepare a campaign;
- request human confirmation before creating a campaign; and
- create a campaign in draft status.

### Tool Calling

The first tool implemented was:

`get_brand_details()`

This introduced tool calling by allowing the agent to retrieve information
from the application instead of relying only on information contained in
the user's prompt.

The second tool implemented was:

`create_campaign()`

This introduced a write operation. The agent can create application data
after receiving confirmation from the user.

### Human-in-the-Loop

Campaign creation currently requires explicit user confirmation before the
`create_campaign()` tool is called.

This provides an approval boundary between AI reasoning and an action that
changes application state.

## Current Limitation

Campaigns are temporarily stored in Python memory.

This means campaign data is lost when the application is restarted.

The next development phase replaces this temporary storage with ClickHouse.

## Next Phase - ClickHouse

The next stage will introduce ClickHouse and cover:

- persistent campaign storage;
- campaign and content data;
- engagement event data;
- agent event data;
- analytical queries;
- real-time campaign analytics; and
- integration with the official ClickHouse MCP server.
