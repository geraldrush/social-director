## Current Architecture

The project currently uses:

* Google Agent Development Kit (ADK)
* Gemini
* Python
* ClickHouse
* Docker

ClickHouse is currently the main persistent data and analytics platform for the application.

The current implemented architecture is:

```text
User
 |
 v
Gemini
 |
 v
Google ADK
 |
 v
Social Media Producer Agent
 |
 v
Application Tools
 |
 v
clickhouse-connect
 |
 v
ClickHouse
 |
 v
social_producer database
```

The first version of the system currently uses one root agent named:

```text
social_media_producer
```

This agent currently handles campaign orchestration.

It can:

* understand a campaign request;
* retrieve stored brand information;
* identify the campaign objective;
* identify the target audience;
* identify the required social platforms;
* identify campaign duration;
* prepare a campaign proposal;
* request missing important information;
* require explicit human confirmation before creating a campaign;
* save approved campaign drafts to ClickHouse; and
* retrieve stored campaigns from ClickHouse.

The project will gradually evolve from this single-agent implementation into a team of specialised agents.

---

## Human-in-the-Loop Campaign Creation

Campaign creation requires explicit confirmation from the user.

The current flow is:

```text
User campaign request
        |
        v
Gemini / ADK Agent
        |
        v
Campaign proposal
        |
        v
Human approval
        |
        v
create_campaign()
        |
        v
create_campaign_record()
        |
        v
ClickHouse
```

The agent must not call `create_campaign()` before explicit user approval.

New campaigns are initially stored with:

```text
status = draft
```

This creates an approval boundary between AI reasoning and actions that modify application state.

The agent is also instructed not to claim that a campaign has been saved unless the database tool successfully performs the write operation.

---

## ClickHouse Integration

ClickHouse is now connected to the AI Social Media Producer.

The first version of campaign storage used temporary Python memory while the ADK tool-calling workflow was being developed.

Campaign storage has now been migrated to ClickHouse.

The current campaign data path is:

```text
Gemini
 |
 v
Google ADK
 |
 v
Application Tool
 |
 v
database.py
 |
 v
clickhouse-connect
 |
 v
HTTP Port 8123
 |
 v
ClickHouse
 |
 v
social_producer.campaigns
```

---

## Persistent ClickHouse Development Environment

ClickHouse runs locally in Docker during development.

The ClickHouse container is:

```text
clickhouse-server
```

The development environment exposes:

```text
8123 - ClickHouse HTTP interface
9000 - ClickHouse native protocol
```

The Python application uses the HTTP interface through port `8123`.

The ClickHouse command-line client normally uses the native protocol through port `9000`.

A persistent Docker volume is now used:

```text
clickhouse-data
```

It is mounted to:

```text
/var/lib/clickhouse
```

This allows ClickHouse database data to survive container replacement.

Previously, removing and recreating the container also removed the database tables and data.

---

## Campaigns Table

The first application table is:

```text
social_producer.campaigns
```

It uses:

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

Important ClickHouse concepts introduced through this table include:

* `MergeTree`
* sorting keys
* `Array(String)`
* `LowCardinality(String)`
* fully qualified database/table names

The sorting key:

```sql
ORDER BY (brand_name, campaign_id)
```

is used by the `MergeTree` engine to organise stored data.

It is not simply a presentation order for query results.

---

## Python and ClickHouse Connection

The Python application uses:

```text
clickhouse-connect
```

Database configuration is stored in environment variables:

```text
CLICKHOUSE_HOST
CLICKHOUSE_PORT
CLICKHOUSE_USER
CLICKHOUSE_PASSWORD
CLICKHOUSE_DATABASE
```

Credentials are stored in:

```text
social_producer/.env
```

The `.env` file is excluded from Git.

Because the environment file is located inside the Python package directory, it is loaded explicitly:

```python
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)
```

The Python-to-ClickHouse connection has been successfully tested.

The server returned:

```text
26.7.4.58
```

The database module currently provides:

```text
test_connection()
get_next_campaign_id()
create_campaign_record()
get_campaigns()
```

---

## Successful Campaign Storage Test

The first campaign successfully stored in ClickHouse was:

```text
Campaign ID:       1
Brand:             BePlugged Tech
Objective:         Generate web development leads
Target Audience:   Small businesses in South Africa
Platforms:         Facebook, LinkedIn
Duration:          14 days
Status:            draft
```

The record was successfully inserted and retrieved using Python.

This initially proved:

```text
Python
 |
 v
clickhouse-connect
 |
 v
ClickHouse
 |
 v
social_producer.campaigns
```

---

## Gemini → ClickHouse Read Path

The agent now has a `list_campaigns()` tool.

This tool retrieves stored campaign information from ClickHouse.

The following path has been successfully tested:

```text
User
 |
 v
Gemini
 |
 v
Google ADK
 |
 v
list_campaigns()
 |
 v
get_campaigns()
 |
 v
ClickHouse
 |
 v
Campaign Data
 |
 v
Gemini Response
```

The agent successfully retrieved the first stored BePlugged Tech campaign.

Therefore:

```text
READ PATH = WORKING
```

---

## Gemini → ClickHouse Write Path

The campaign creation path has also been tested successfully.

A second campaign was requested with:

```text
Brand:           BePlugged Tech
Objective:       Promote IT training
Target Audience: Technology learners in South Africa
Platforms:       Facebook, LinkedIn
Duration:        7 days
```

The agent first prepared the campaign proposal and requested confirmation.

After receiving explicit user approval, the campaign was stored in ClickHouse.

The successful write path is:

```text
User
 |
 v
Gemini / ADK
 |
 v
Campaign Proposal
 |
 v
Human Confirmation
 |
 v
create_campaign()
 |
 v
create_campaign_record()
 |
 v
ClickHouse
```

ClickHouse now contains two campaign records.

Therefore:

```text
READ PATH  = WORKING
WRITE PATH = WORKING
```

This proves that Gemini can both retrieve application state from ClickHouse and create persistent application data through controlled ADK tool calls.

---

## Target Multi-Agent Architecture

The current implementation intentionally starts with one root agent.

As the system grows, responsibilities will be separated into specialised agents instead of continuously adding responsibilities to one large agent.

The planned architecture is:

```text
                         User
                          |
                          v
                Social Media Producer
                    / Orchestrator
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
      Strategy         Content         Analytics
       Agent            Agent            Agent
                          |               |
                    +-----+-----+         v
                    |           |     Optimisation
                    v           v         Agent
               Generation    Review
                  Agent        Agent
                    |           |
                    +-----+-----+
                          |
                          v
                      ClickHouse
                +---------+----------+
                |         |          |
                v         v          v
            campaigns   content   engagement
                                   events

                          +
                     agent_events
```

The existing `social_media_producer` agent is expected to evolve into the orchestrator rather than being discarded.

Specialised responsibilities will gradually move into dedicated agents as each part of the workflow is implemented and tested.

---

## Why ClickHouse Is Central to the Architecture

ClickHouse is not being added only as a storage layer.

The project intends to use ClickHouse as the central analytical and event platform connecting the agent workflow.

The current `campaigns` table is the first step.

Future data models will introduce:

```text
campaigns
content_items
engagement_events
agent_events
```

These datasets will support:

* campaign analytics;
* content-performance analytics;
* high-volume engagement event ingestion;
* agent execution/event analysis;
* campaign comparisons;
* time-series analysis;
* aggregations;
* materialized views where justified;
* near-real-time analytical queries;
* optimisation recommendations; and
* ClickHouse MCP integration.

These capabilities are planned and should not yet be considered implemented.

---

## Current Development Status

Completed:

```text
[✓] Initial Google ADK agent
[✓] Gemini integration
[✓] Brand information tool
[✓] Campaign creation tool
[✓] Human approval before campaign creation
[✓] Local ClickHouse Docker environment
[✓] Dedicated social_producer database
[✓] Dedicated ClickHouse application user
[✓] campaigns MergeTree table
[✓] Python-to-ClickHouse connection
[✓] Environment-based database configuration
[✓] Persistent Docker volume
[✓] Python campaign insert
[✓] Python campaign retrieval
[✓] Gemini/ADK campaign retrieval
[✓] Gemini/ADK campaign creation
[✓] End-to-end ClickHouse read path
[✓] End-to-end ClickHouse write path
```

Not yet implemented:

```text
[ ] content_items data model
[ ] content planning workflow
[ ] specialised content agent
[ ] content generation workflow
[ ] review agent
[ ] engagement event ingestion
[ ] agent event logging
[ ] analytics agent
[ ] campaign analytics
[ ] materialized views
[ ] optimisation agent
[ ] ClickHouse MCP integration
[ ] complete multi-agent orchestration
[ ] production Google Cloud deployment
```

---

## Next Development Phase

The next development milestone is the campaign content model.

The relationship will begin with:

```text
campaigns
    |
    | one-to-many
    v
content_items
```

The goal of this phase is to give campaigns persistent content records before introducing specialised content-planning and generation agents.

The implementation process remains:

```text
Build one meaningful component
        |
        v
Test it
        |
        v
Understand what happened
        |
        v
Fix problems
        |
        v
Document lessons learned
        |
        v
Commit
        |
        v
Proceed
```

