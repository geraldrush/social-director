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


## ClickHouse Integration

ClickHouse is being used as the primary data and analytics platform for the project.

The project initially stored campaign data temporarily in a Python list. This was useful for learning how ADK tools can perform write operations, but the data was lost whenever the application restarted.

The next stage replaces temporary in-memory storage with ClickHouse.

### Local ClickHouse Environment

ClickHouse is currently running locally in Docker during development.

The container exposes:

* Port `8123` for the ClickHouse HTTP interface
* Port `9000` for the native ClickHouse protocol

The ClickHouse server is started using:

```bash
docker run -d \
  --name clickhouse-server \
  -p 8123:8123 \
  -p 9000:9000 \
  clickhouse/clickhouse-server:latest
```

The ClickHouse client can be opened using:

```bash
docker exec -it clickhouse-server clickhouse-client
```

### Project Database

A dedicated database has been created for the application:

```sql
CREATE DATABASE social_producer;
```

The database contains the operational and analytical data used by the AI Social Media Producer.

### Campaigns Table

The first ClickHouse table is `campaigns`.

```sql
CREATE TABLE campaigns
(
    campaign_id UInt64,
    brand_name String,
    objective String,
    target_audience String,
    platforms Array(String),
    duration_days UInt16,
    status LowCardinality(String),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (brand_name, campaign_id);
```

### ClickHouse Concepts Introduced

#### MergeTree

The `campaigns` table uses the `MergeTree` table engine.

MergeTree is one of the core ClickHouse table-engine families and is designed for efficient data storage and analytical querying.

The project will make greater use of MergeTree capabilities as campaign, content, engagement and agent-event data are introduced.

#### Sorting Key

The table uses:

```sql
ORDER BY (brand_name, campaign_id)
```

In a ClickHouse `MergeTree` table, `ORDER BY` is not simply used to control how query results are displayed.

It defines the table's sorting key and influences how data is physically organised for efficient retrieval.

The initial sorting key was chosen because campaign queries are expected to frequently filter or group data by brand.

#### LowCardinality

Campaign status is stored as:

```sql
status LowCardinality(String)
```

Campaign records are expected to reuse a relatively small set of status values such as:

* `draft`
* `approved`
* `scheduled`
* `active`
* `completed`
* `cancelled`

`LowCardinality(String)` is therefore used instead of a normal `String` so ClickHouse can store repeated values more efficiently.

#### Array Data Type

Social media platforms are stored as:

```sql
platforms Array(String)
```

This allows one campaign to contain multiple platforms, for example:

```text
["Facebook", "LinkedIn"]
```

without requiring an additional table for the current implementation.

### Current Architecture

```text
Social Media Producer Agent
          |
       Gemini
          |
      Google ADK
          |
   Application Tools
          |
      ClickHouse
```

At this stage the agent is not yet connected to ClickHouse.

The current goal is to understand and validate the ClickHouse data model manually before giving the AI agents database access.

### Next Steps

The next development steps are:

1. Insert the first campaign into ClickHouse manually.
2. Query the campaign using ClickHouse SQL.
3. Connect Python to ClickHouse.
4. Replace the temporary Python campaign list with persistent ClickHouse storage.
5. Introduce content and engagement event tables.
6. Integrate the official ClickHouse MCP server.
7. Allow Gemini agents to query campaign analytics through MCP.

