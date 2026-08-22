# AI Social Media Producer

An agentic social-media campaign production system built with **Google Gemini**, **Google Agent Development Kit (ADK)**, **Python**, and **ClickHouse**.

The project is being developed for the **Google Cloud / Gemini Agentic Cinema Hackathon**.

AI Social Media Producer treats social-media campaign production as an intelligent media workflow. Instead of using a single chatbot to perform every task, the system is being developed as a team of specialised AI agents coordinated by a central Social Media Producer.

ClickHouse serves as the project's persistent data and analytics platform.

---

## Project Goals

The system is being designed to eventually support:

- brand and campaign understanding;
- campaign strategy;
- social-media content planning;
- AI-assisted content generation;
- human approval workflows;
- campaign and content storage;
- engagement-event ingestion;
- campaign analytics;
- agent activity analysis;
- campaign optimisation;
- multi-agent orchestration; and
- ClickHouse MCP integration.

The project is being built incrementally.

Features described as planned are not considered implemented until they have been built and tested.

---

## Current Implementation

The current working implementation includes:

- a Google ADK root agent called `social_media_producer`;
- Gemini integration;
- ClickHouse persistent campaign storage;
- human approval before campaign creation;
- campaign read and write tools;
- a `campaigns` ClickHouse table;
- a `content_items` ClickHouse table;
- Python-to-ClickHouse campaign and content operations;
- a specialist `content_planner` agent;
- root-agent to specialist-agent delegation; and
- persistent ClickHouse storage using a Docker volume.

The current multi-agent implementation is:

```text
User
 |
 v
Social Media Producer
     Orchestrator
 |
 | delegates content-planning work
 v
Content Planning Agent
 |
 +-----------------------+
 |                       |
 v                       v
Campaign Data       Existing Content
 |                       |
 +-----------+-----------+
             |
             v
         ClickHouse
```

Additional specialist agents will be introduced incrementally.

---

## Planned Agent Architecture

The target architecture is:

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
       Agent           Planning          Agent
                        Agent              |
                          |                v
                          |          Optimisation
                          |              Agent
                          v
                    Generation Agent
                          |
                          v
                     Review Agent
                          |
                          v
                      ClickHouse
```

Currently implemented:

```text
Social Media Producer / Orchestrator    [✓]
    |
    +--- Content Planning Agent         [✓]

Strategy Agent                          [ ]
Content Generation Agent                [ ]
Review Agent                            [ ]
Analytics Agent                         [ ]
Optimisation Agent                      [ ]
```

---

# Local Development Setup

## Prerequisites

The development environment requires:

- Python 3
- Git
- Docker
- Google Gemini API access
- Google Agent Development Kit (ADK)

ClickHouse currently runs locally using Docker.

---

## 1. Clone the Repository

Using SSH:

```bash
git clone git@github.com:geraldrush/social-director.git
cd social-director
```

---

## 2. Create the Python Virtual Environment

Create the virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

The `.venv` directory must not be committed to Git.

---

## 3. Create the Environment File

Application credentials and configuration are stored outside the source code.

Create:

```text
social_producer/.env
```

A development configuration requires values for:

```dotenv
GOOGLE_API_KEY=your_google_api_key

CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=social_producer
CLICKHOUSE_PASSWORD=your_clickhouse_password
CLICKHOUSE_DATABASE=social_producer
```

Do **not** commit `.env`.

The repository should contain an `.env.example` containing only safe placeholders.

The application explicitly loads the environment file from the `social_producer` directory.

---

# ClickHouse Local Setup

## 4. Create Persistent ClickHouse Storage

Create a Docker volume:

```bash
docker volume create clickhouse-data
```

The volume is used to preserve ClickHouse data when the container is replaced.

It is mounted inside the container at:

```text
/var/lib/clickhouse
```

---

## 5. Start ClickHouse

Create the local ClickHouse container:

```bash
docker run -d \
  --name clickhouse-server \
  --restart unless-stopped \
  -p 8123:8123 \
  -p 9000:9000 \
  -v clickhouse-data:/var/lib/clickhouse \
  -e CLICKHOUSE_USER=social_producer \
  -e CLICKHOUSE_PASSWORD="your_clickhouse_password" \
  clickhouse/clickhouse-server:latest
```

Replace:

```text
your_clickhouse_password
```

with your local development password.

Never commit the real password to Git.

---

## 6. Verify the Container

Check that ClickHouse is running:

```bash
docker ps
```

If ClickHouse does not appear ready, inspect the logs:

```bash
docker logs clickhouse-server
```

A Docker container showing as `Up` does not necessarily mean that the service inside it is ready to accept connections.

---

## 7. ClickHouse Ports

The local environment exposes:

```text
8123    HTTP interface
9000    Native ClickHouse protocol
```

The Python application currently connects through:

```text
8123
```

using `clickhouse-connect`.

The ClickHouse command-line client normally communicates through:

```text
9000
```

---

## 8. Open the ClickHouse Client

Run:

```bash
docker exec -it clickhouse-server \
  clickhouse-client \
  --user social_producer \
  --password
```

Enter the password configured when the container was created.

---

## 9. Create the Application Database

Inside ClickHouse:

```sql
CREATE DATABASE IF NOT EXISTS social_producer;
```

Then select it:

```sql
USE social_producer;
```

---

# Database Schema

## Campaigns

Create the campaign table:

```sql
CREATE TABLE IF NOT EXISTS social_producer.campaigns
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

The sorting key is:

```sql
ORDER BY (brand_name, campaign_id)
```

In ClickHouse this is not simply presentation ordering. It influences how the `MergeTree` table physically organises data for analytical access.

---

## Content Items

Create the content table:

```sql
CREATE TABLE IF NOT EXISTS social_producer.content_items
(
    content_id UInt64,
    campaign_id UInt64,
    platform LowCardinality(String),
    content_type LowCardinality(String),
    topic String,
    content_text String,
    status LowCardinality(String),
    scheduled_at Nullable(DateTime),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (campaign_id, platform, content_id);
```

The current relationship is:

```text
campaigns
    |
    | 1:N
    v
content_items
```

A campaign can therefore contain multiple content items.

---

## 10. Verify the Database

Inside the ClickHouse client:

```sql
USE social_producer;

SHOW TABLES;
```

The current implementation should contain:

```text
campaigns
content_items
```

Inspect either table with:

```sql
DESCRIBE TABLE campaigns;
```

or:

```sql
DESCRIBE TABLE content_items;
```

---

# Test the Python Connection

With the virtual environment active:

```bash
python -c "from social_producer.database import test_connection; print(test_connection())"
```

A successful response should return the running ClickHouse server version.

---

## Test Campaign Retrieval

```bash
python -c "from social_producer.database import get_campaigns; print(get_campaigns())"
```

---

## Test Content Retrieval

```bash
python -c "from social_producer.database import get_content_items; print(get_content_items())"
```

---

# Run the Agent Locally

With the Python environment activated:

```bash
adk web
```

Open the ADK development interface and select:

```text
social_producer
```

The ADK Web interface is currently used for local development and testing.

---

# Project Structure

The project currently has approximately the following structure:

```text
social-director/
|
├── README.md
├── requirements.txt
├── .gitignore
|
├── .venv/                         # local only / ignored
|
└── social_producer/
    ├── __init__.py
    ├── agent.py
    ├── content_planner.py
    ├── database.py
    ├── .env                       # local only / ignored
    └── .gitignore
```

As additional specialist agents are introduced, the structure will evolve.

---

# Current Data Architecture

Implemented:

```text
campaigns
    |
    | 1:N
    v
content_items
```

Planned:

```text
campaigns
    |
    v
content_items
    |
    | 1:N
    v
engagement_events

agent_events
```

`engagement_events` and `agent_events` have **not yet been implemented**.

They are intended to become the event-oriented foundation for deeper ClickHouse analytics.

---

# Security

The following must never be committed:

```text
.env
.venv/
API keys
ClickHouse passwords
Google Cloud credentials
service-account credentials
```

Secrets should be supplied through environment configuration during local development and through an appropriate secret-management system when the application is deployed.

Before committing changes, verify ignored files with:

```bash
git status
git check-ignore -v social_producer/.env
```

---

# Development Approach

The project follows an incremental development process:

```text
Build one meaningful component
        |
        v
Test it
        |
        v
Understand the result
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

This is intentional.

The hackathon submission should demonstrate working functionality and technical understanding rather than presenting planned functionality as though it has already been implemented.

---

# Current Milestone

Completed:

```text
[✓] Google ADK root agent
[✓] Gemini integration
[✓] Human-in-the-loop campaign creation
[✓] Local ClickHouse environment
[✓] Persistent ClickHouse Docker volume
[✓] campaigns MergeTree table
[✓] content_items MergeTree table
[✓] Python-to-ClickHouse connection
[✓] Campaign read/write path
[✓] Content read/write path
[✓] Content Planning Agent
[✓] Root-agent to specialist-agent delegation
```

In progress:

```text
[~] Content-planning factual grounding
```

Next:

```text
[ ] Approved content-plan persistence
[ ] Content Generation Agent
[ ] Review Agent
[ ] Engagement event ingestion
[ ] Agent event logging
[ ] ClickHouse analytics
[ ] Materialized views where justified
[ ] Analytics Agent
[ ] Optimisation Agent
[ ] ClickHouse MCP integration
[ ] Google Cloud deployment
```

---

# Current Limitations

The current implementation does **not** yet:

- publish content to social-media platforms;
- schedule social-media posts;
- ingest real engagement events;
- generate final production-ready social-media content through a dedicated generation agent;
- perform automated campaign optimisation;
- provide production Google Cloud deployment;
- use ClickHouse MCP; or
- provide the complete planned multi-agent architecture.

These capabilities remain part of the development roadmap.

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

## Content Planning and Multi-Agent Orchestration

The project has started evolving from a single-agent implementation into a specialised multi-agent architecture.

The original `social_media_producer` agent remains the root agent and is being developed into the system orchestrator.

The first specialist agent introduced is:

```text
content_planner
```

Its responsibility is to determine **what content should be produced for an existing campaign**.

The Content Planning Agent does not currently:

* generate final social-media copy;
* publish content;
* schedule content;
* modify campaigns; or
* write content plans to ClickHouse.

This separation is intentional. Content planning and content generation will eventually be handled as different responsibilities.

### Current Multi-Agent Architecture

The currently implemented agent architecture is:

```text
User
 |
 v
Social Media Producer
    Orchestrator
 |
 | delegates content-planning requests
 v
Content Planning Agent
 |
 +-------------------+
 |                   |
 v                   v
Campaign Data    Existing Content
 |                   |
 +---------+---------+
           |
           v
       ClickHouse
```

The `social_media_producer` registers the Content Planning Agent as a specialist sub-agent.

When a request concerns content planning for an existing campaign, the root agent can delegate the task to the specialist rather than performing the specialist's reasoning itself.

This is the first implemented step toward the planned team-of-agents architecture.

---

## Content Items

A new ClickHouse table has been introduced:

```text
social_producer.content_items
```

The table stores individual pieces of content associated with campaigns.

The current relationship is:

```text
campaigns
    |
    | 1:N
    v
content_items
```

One campaign can therefore contain multiple planned or generated content items.

The table currently uses:

```sql
CREATE TABLE social_producer.content_items
(
    content_id UInt64,
    campaign_id UInt64,
    platform LowCardinality(String),
    content_type LowCardinality(String),
    topic String,
    content_text String,
    status LowCardinality(String),
    scheduled_at Nullable(DateTime),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (campaign_id, platform, content_id);
```

The sorting key begins with `campaign_id` because content will frequently be retrieved and analysed in the context of a campaign.

`platform`, `content_type`, and `status` use `LowCardinality(String)` because these fields are expected to repeatedly use a relatively small set of values.

`schedule_at` is represented by `Nullable(DateTime)` so unscheduled content can exist without requiring an artificial scheduling date.

---

## Content Data Access

The Python ClickHouse data layer now includes:

```text
get_next_content_id()
create_content_item()
get_content_items()
```

These functions extend the existing campaign data layer.

The current tested content data path is:

```text
Python
 |
 v
database.py
 |
 v
clickhouse-connect
 |
 v
ClickHouse
 |
 v
social_producer.content_items
```

Manual and Python-based tests have confirmed:

```text
[✓] Manual content insert into ClickHouse
[✓] Manual content retrieval from ClickHouse
[✓] Python content retrieval
[✓] Python next-content-ID generation
[✓] Python content insertion
```

Content records have successfully been associated with Campaign 2 using `campaign_id`.

---

## Content Planning Agent

The first specialist agent is implemented in:

```text
social_producer/content_planner.py
```

The agent can access campaign and existing-content information through read-only tools.

Its current data flow is:

```text
Content Planning Agent
        |
        +------------------------+
        |                        |
        v                        v
get_campaign_by_id()    list_campaign_content()
        |                        |
        +-----------+------------+
                    |
                    v
                ClickHouse
```

The agent currently does not have access to `create_content_item()`.

This is intentional.

The Content Planning Agent was first tested as a read-only agent before being given any capability that changes application state.

---

## Standalone Content Planner Test

Before integrating the planner with the root producer, it was tested independently.

The test request asked the agent to create a content plan for Campaign 2.

The agent successfully:

* retrieved Campaign 2;
* identified the campaign objective;
* identified the target audience;
* identified Facebook and LinkedIn as campaign platforms;
* recognised the seven-day campaign duration;
* retrieved existing content items;
* recognised that educational content already existed;
* avoided simply repeating the same content strategy; and
* produced a structured multi-day content plan.

The test confirmed that the planner could reason using application data stored in ClickHouse.

---

## First Multi-Agent Delegation

After the standalone test succeeded, `content_planner` was registered as a sub-agent of the root `social_media_producer`.

A content-planning request was then submitted to the root agent:

```text
Create a content plan for campaign 2.
```

The request was successfully handled through the multi-agent workflow.

The resulting architecture is:

```text
User
 |
 v
Social Media Producer
 |
 | delegation
 v
Content Planning Agent
 |
 +------------------+
 |                  |
 v                  v
Campaign        Existing Content
 |                  |
 +---------+--------+
           |
           v
       ClickHouse
           |
           v
      Content Plan
```

This proves the project's first working specialist-agent delegation path.

The project is therefore no longer only a single LLM agent with application tools.

It now contains an orchestrator and a specialised agent with a defined responsibility.

---

## Grounding Lesson

Testing the Content Planning Agent revealed an important issue.

Although the planner correctly used campaign information, some proposed ideas relied on business information that had not been supplied.

Examples included concepts involving:

* learner testimonials;
* specific courses;
* enrolment deadlines;
* training schedules; and
* other business claims.

These were not established by the available campaign data.

The planner instructions are therefore being strengthened with factual-grounding rules.

The Content Planning Agent must not invent brand or campaign facts.

If a potentially useful content idea requires unavailable information, the agent should identify it as:

```text
REQUIRES BRAND INFORMATION
```

rather than presenting hypothetical information as fact.

This distinction will also influence the future Review Agent, which will be responsible for detecting unsupported claims before content can be approved.

---

## Current Agent Status

Implemented:

```text
Social Media Producer / Orchestrator    [✓]
        |
        +--- Content Planning Agent     [✓]
```

Planned:

```text
Social Media Producer / Orchestrator
        |
        +--- Strategy Agent             [ ]
        |
        +--- Content Planning Agent     [✓]
        |
        +--- Content Generation Agent   [ ]
        |
        +--- Review Agent               [ ]
        |
        +--- Analytics Agent            [ ]
        |
        +--- Optimisation Agent         [ ]
```

Agents will be introduced incrementally as their corresponding data models and workflows are implemented and tested.

---

## Current Data Architecture

The implemented ClickHouse data model is now:

```text
campaigns
    |
    | 1:N
    v
content_items
```

Future event-oriented data will extend this with:

```text
campaigns
    |
    v
content_items
    |
    v
engagement_events     [planned]

agent_events           [planned]
```

The high-volume engagement and agent-event datasets will later provide the foundation for deeper ClickHouse analytics.

---

## Development Milestone

The project has now demonstrated:

```text
Gemini                               [✓]
Google ADK                           [✓]
ClickHouse persistent storage        [✓]
Campaign read path                   [✓]
Campaign write path                  [✓]
Human-in-the-loop campaign approval  [✓]
Content storage model                [✓]
Python content read/write            [✓]
Specialist Content Planning Agent    [✓]
Multi-agent delegation               [✓]
Grounded-planning rules              [in progress]
```

The next development objective is to complete the grounding test and then design a controlled workflow for converting an approved content plan into persistent `content_items`.

The Content Planning Agent will not be given unrestricted write access without first defining the approval boundary for this action.

## Approved Content Plan Persistence

The content-planning workflow now includes a human approval boundary before planned content is written to ClickHouse.

The implemented flow is:

```text
User
 |
 v
Social Media Producer / Orchestrator
 |
 v
Content Planning Agent
 |
 v
Grounded Content Plan
 |
 v
Human Review
 |
 v
Explicit Approval
 |
 v
save_content_plan()
 |
 v
create_content_item()
 |
 v
ClickHouse
 |
 v
status = planned
```

The Content Planning Agent does not directly persist its own recommendations.

Instead, the root `social_media_producer` controls the write operation after explicit user approval.

This preserves the same human-in-the-loop principle already used for campaign creation.

---

## Content Planning Schema Evolution

Testing the Content Planning Agent revealed that the initial `content_items` schema did not preserve all of the information produced by the planner.

The planner produces information such as:

```text
platform
content_type
topic
suggested campaign day
content purpose
```

The original table did not contain dedicated fields for:

```text
campaign_day
content_purpose
```

The schema was therefore evolved by adding:

```sql
campaign_day Nullable(UInt16)
```

and:

```sql
content_purpose String DEFAULT ''
```

The current content structure includes:

```text
content_id
campaign_id
platform
content_type
topic
campaign_day
content_purpose
content_text
status
scheduled_at
created_at
```

This allows planning metadata to be persisted before final social-media copy is generated.

---

## Planned Content Lifecycle

The project now distinguishes between content planning and content generation.

A newly approved planned item is stored with:

```text
status = planned
content_text = ""
```

The intended lifecycle is:

```text
planned
   |
   v
Content Generation
   |
   v
draft
   |
   v
Review
   |
   v
approved
   |
   v
scheduled
   |
   v
published
```

Only the `planned` stage is currently implemented as part of this workflow.

Generation, review, approval, scheduling and publishing remain future stages.

---

## Why Planned Content Has Empty Copy

The Content Planning Agent is responsible for deciding **what content should be created**.

It is not responsible for producing final social-media copy.

For this reason, a planned item can exist with:

```text
content_text = ""
```

The future Content Generation Agent will be responsible for filling this field.

This keeps agent responsibilities separated:

```text
Content Planning Agent
        |
        v
Decides WHAT should be produced
        |
        v
Human approval
        |
        v
Planned content stored in ClickHouse
        |
        v
Content Generation Agent
        |
        v
Writes the actual content
```

---

## Approval-Controlled Write Tool

The root producer now has a controlled content-plan persistence tool.

The tool:

```text
save_content_plan()
```

creates one approved planned content item.

Internally, it calls:

```text
create_content_item()
```

with:

```text
status = planned
content_text = ""
```

The tool must only be called after explicit user approval.

The root agent is instructed to:

* present the proposed content plan first;
* wait for explicit user approval;
* save only approved items;
* avoid interpreting silence as approval;
* preserve `planned` status;
* keep final copy empty at this stage; and
* never claim that content was generated, scheduled or published.

---

## Selective Approval

The approval workflow supports selective approval.

The user does not have to approve the full proposed content plan.

For example:

```text
Approve and save only the Day 3 LinkedIn awareness item.
```

should result in only that item being written to ClickHouse.

Other proposed items must remain unsaved.

This behaviour was successfully tested.

---

## Grounded Planning Test

Before persistence was enabled, the Content Planning Agent was strengthened with grounding rules.

If an idea depends on unavailable business information, the planner must mark it as:

```text
REQUIRES BRAND INFORMATION
```

instead of inventing facts.

Examples of information that must not be invented include:

* testimonials;
* customer success stories;
* exact courses;
* pricing;
* enrolment deadlines;
* schedules;
* statistics;
* certifications;
* partnerships; and
* business claims not supported by available data.

After updating the grounding instructions, the planner successfully produced a content plan that distinguished between:

```text
Known campaign information
```

and:

```text
Ideas requiring additional brand information
```

---

## Successful Approved Content Test

Campaign 2 was used to test the complete workflow.

The planner proposed several content ideas.

The user approved only the Day 3 LinkedIn awareness item.

The approved item contained:

```text
Campaign ID:      2
Platform:         LinkedIn
Campaign Day:     3
Content Type:     awareness
Topic:            The growing demand for IT professionals in South Africa
Content Purpose:  Highlight the industry demand and employment landscape for tech learners.
```

The system saved only this approved item.

ClickHouse assigned:

```text
Content ID: 5
```

The persisted record was independently verified from Python.

The stored state was:

```text
content_id:       5
campaign_id:      2
platform:         LinkedIn
content_type:     awareness
campaign_day:     3
content_text:     ""
status:           planned
scheduled_at:     None
```

No other proposed content items were saved.

---

## Proven End-to-End Workflow

The project has now demonstrated:

```text
User
 |
 v
Social Media Producer / Orchestrator
 |
 v
Content Planning Agent
 |
 v
Campaign + Existing Content
 |
 v
ClickHouse
 |
 v
Grounded Content Plan
 |
 v
Human Approval
 |
 v
save_content_plan()
 |
 v
create_content_item()
 |
 v
ClickHouse
 |
 v
Planned Content
```

This is the first fully tested workflow combining:

```text
[✓] Multi-agent delegation
[✓] ClickHouse reads
[✓] Agent reasoning
[✓] Grounded planning
[✓] Human approval
[✓] Selective approval
[✓] Controlled tool execution
[✓] ClickHouse writes
[✓] Independent database verification
```

---

## Current Agent Responsibilities

```text
Social Media Producer / Orchestrator
    |
    +--- Campaign workflow
    |
    +--- Human approval control
    |
    +--- Content-plan persistence
    |
    +--- Content Planning Agent
```

The next planned specialist is:

```text
Content Generation Agent
```

Its responsibility will be to convert approved planned content into actual platform-specific social-media copy.

It will not be responsible for final approval or publishing.

---

## Next Development Milestone

The next milestone is:

```text
Planned Content
      |
      v
Content Generation Agent
      |
      v
Generated Copy
      |
      v
status = draft
      |
      v
Future Review Agent
```

The Content Generation Agent will be introduced incrementally using the same development approach:

```text
Build
 |
 v
Test
 |
 v
Verify
 |
 v
Document
 |
 v
Commit
 |
 v
Proceed
```
---

# Content Generation Agent Milestone

The project now includes a second specialist agent:

```text
content_generator
```

The Content Generation Agent is responsible for converting approved planned content into platform-specific draft social-media copy.

This extends the multi-agent architecture from:

```text
Social Media Producer / Orchestrator
        |
        +--- Content Planning Agent
```

to:

```text
Social Media Producer / Orchestrator
        |
        +--- Content Planning Agent
        |
        +--- Content Generation Agent
```

The two specialists have deliberately separate responsibilities.

```text
Content Planning Agent
        |
        v
Decides WHAT content should be created


Content Generation Agent
        |
        v
Decides HOW the actual post should be written
```

This separation prevents a single agent from controlling the entire content-production workflow.

---

## Content Generation Workflow

The implemented workflow is:

```text
User
 |
 v
Social Media Producer / Orchestrator
 |
 | delegation
 v
Content Generation Agent
 |
 +------------------------+
 |                        |
 v                        v
Content Item          Campaign Context
 |                        |
 +-----------+------------+
             |
             v
         ClickHouse
             |
             v
      Draft Generation
             |
             v
        Human Review
             |
             v
      Explicit Approval
             |
             v
   save_content_draft()
             |
             v
       ClickHouse Update
             |
             v
       status = draft
```

The Content Generation Agent does not have direct database write access.

The root Social Media Producer controls persistence after explicit human approval.

---

## Content Lookup

A new database function was introduced:

```text
get_content_item_by_id()
```

This retrieves an individual content item from ClickHouse using its `content_id`.

The function returns the planning and content information associated with the item, including:

```text
content_id
campaign_id
platform
content_type
topic
campaign_day
content_purpose
content_text
status
scheduled_at
created_at
```

This allows specialist agents to work with a specific content item rather than loading an entire campaign's content collection.

---

## Content Generator Context

Before generating copy, the Content Generation Agent retrieves:

1. the requested content item; and
2. the campaign associated with that content item.

The resulting context includes information such as:

```text
Brand
Campaign objective
Target audience
Platform
Content type
Topic
Campaign day
Content purpose
Current content status
```

This allows generated content to remain aligned with both the planned item and its parent campaign.

---

## Platform-Aware Generation

The Content Generation Agent applies platform-specific guidance.

For Facebook, generated content should generally be:

```text
conversational
accessible
engaging
interaction-oriented
```

For LinkedIn, generated content should generally be:

```text
professional
useful
credible
career/professional audience appropriate
```

This behaviour will evolve as additional platforms are introduced.

---

## Content Generation Grounding

Testing revealed an important grounding issue.

One planned content item contained the topic:

```text
The growing demand for IT professionals in South Africa
```

The first generated draft treated the topic itself as evidence that demand for IT professionals was increasing.

This exposed an important distinction:

```text
PLANNED TOPIC
     !=
VERIFIED FACT
```

A content topic describes what an item is intended to discuss.

It does not prove that factual claims contained in the topic are true.

The Content Generation Agent's grounding instructions were therefore strengthened.

The generator must not treat either:

```text
topic
```

or:

```text
content_purpose
```

as factual evidence.

Claims involving areas such as:

```text
market growth
employment growth
industry trends
statistics
customer success
improved outcomes
```

require supporting information before they can be presented as established facts.

---

## Grounding Failure Test

Content ID 5 was used to test this behaviour.

The planned item was:

```text
Content ID:       5
Campaign ID:      2
Platform:         LinkedIn
Content Type:     awareness
Campaign Day:     3

Topic:
The growing demand for IT professionals in South Africa

Purpose:
Highlight the industry demand and employment landscape
for tech learners.
```

The Content Generation Agent correctly identified that the requested topic would require verified supporting information.

Instead of inventing employment statistics, industry reports, or market trends, it returned a grounding warning and requested verified information.

This confirmed:

```text
Unsupported factual premise detected       [✓]
Statistics were not invented                [✓]
Market claims were not fabricated           [✓]
Additional evidence was requested           [✓]
Database remained unchanged                 [✓]
```

Content ID 5 remained:

```text
status = planned
content_text = ""
```

---

## Grounded Generation Test

A second planned item was selected that did not require unsupported external facts.

Content ID 4 contained:

```text
Campaign ID:      2
Platform:         Facebook
Content Type:     engagement
Campaign Day:     4

Topic:
Which IT skill would you most like to learn?

Purpose:
Encourage technology learners to share which practical
IT skills they are most interested in learning.
```

The Content Generation Agent successfully generated Facebook copy for this item.

Because the post was primarily an engagement question, the generator could produce useful content without inventing statistics, testimonials, prices, deadlines, or other unsupported business information.

---

## Read-Only Generation Boundary

After draft generation, Content ID 4 was checked directly in ClickHouse through the Python data layer.

It remained:

```text
content_text = ""
status = planned
```

This confirmed that generation alone does not modify persistent application state.

The boundary is therefore:

```text
Content Generation Agent
        |
        v
Generate proposal
        |
        X
   NO DATABASE WRITE
        |
        v
Human must approve first
```

---

## Approved Draft Persistence

After proving the read-only generation workflow, controlled draft persistence was introduced.

The database layer now contains:

```text
save_generated_content()
```

The root orchestrator exposes the controlled agent tool:

```text
save_content_draft()
```

The Content Generation Agent itself does not receive this write tool.

The responsibility boundary is:

```text
Content Generation Agent
        |
        v
Generate draft
        |
        v
Return draft to user
        |
        v
Human approval
        |
        v
Social Media Producer
        |
        v
save_content_draft()
        |
        v
save_generated_content()
        |
        v
ClickHouse
```

This preserves human control over persistent state changes.

---

## Planned-to-Draft State Transition

When an approved generated draft is persisted, the content item transitions from:

```text
status = planned
content_text = ""
```

to:

```text
status = draft
content_text = "<approved generated copy>"
```

This creates the first implemented content lifecycle transition:

```text
planned
   |
   | Content Generation Agent
   |
   v
Generated Proposal
   |
   | Human approval
   |
   v
draft
```

Future stages remain:

```text
draft
  |
  v
review
  |
  v
approved
  |
  v
scheduled
  |
  v
published
```

These later transitions have not yet been implemented.

---

## ClickHouse Update Behaviour

Campaign and content creation primarily use inserts.

Saving generated content is different because the existing `content_items` row must transition from `planned` to `draft`.

The current implementation performs a ClickHouse update mutation to change:

```text
content_text
status
```

for the existing content item.

Conceptually:

```text
Existing ClickHouse Row

content_id = 4
content_text = ""
status = planned

        |
        | approved draft
        v

Updated ClickHouse Row

content_id = 4
content_text = "<generated copy>"
status = draft
```

This introduced another ClickHouse concept into the project: mutation of existing analytical data rather than only append operations.

As the project evolves, the suitability of mutations versus event-based state tracking can be revisited.

---

## Successful End-to-End Generation Test

Content ID 4 was used for the complete workflow.

The Social Media Producer delegated generation to the Content Generation Agent.

The specialist generated Facebook copy.

Before approval, the database was independently checked and still contained:

```text
content_text = ""
status = planned
```

The user then explicitly approved the generated draft.

The Social Media Producer persisted the approved copy.

A second independent database query confirmed:

```text
content_id = 4
status = draft
content_text = "<approved Facebook copy>"
```

The original planning metadata remained associated with the same content item.

---

## Proven Content Generation Workflow

The project has now demonstrated:

```text
User
 |
 v
Social Media Producer / Orchestrator
 |
 v
Content Generation Agent
 |
 v
Content + Campaign Retrieval
 |
 v
ClickHouse
 |
 v
Grounding Check
 |
 v
Platform-Specific Draft
 |
 v
Human Review
 |
 v
Explicit Approval
 |
 v
Social Media Producer
 |
 v
save_content_draft()
 |
 v
ClickHouse Mutation
 |
 v
status = draft
```

The following capabilities have therefore been tested:

```text
[✓] Second specialist agent
[✓] Root-to-generator delegation
[✓] Individual content lookup
[✓] Campaign-context retrieval
[✓] Platform-aware generation
[✓] Content grounding
[✓] Unsupported-claim detection
[✓] Read-only generation
[✓] Human approval
[✓] Controlled database write
[✓] planned → draft transition
[✓] Independent database verification
```

---

## Current Multi-Agent Architecture

The implemented architecture is now:

```text
                    User
                     |
                     v
          Social Media Producer
             / Orchestrator
                     |
          +----------+----------+
          |                     |
          v                     v
 Content Planning Agent   Content Generation Agent
          |                     |
          v                     v
   Content Strategy        Draft Copy
          |                     |
          +----------+----------+
                     |
                     v
                 ClickHouse
```

Current specialist status:

```text
Social Media Producer / Orchestrator    [✓]
        |
        +--- Content Planning Agent     [✓]
        |
        +--- Content Generation Agent   [✓]
        |
        +--- Review Agent               [ ]
        |
        +--- Analytics Agent            [ ]
        |
        +--- Optimisation Agent         [ ]
```

---

## Human-in-the-Loop Boundaries

The project now contains two separate approval boundaries.

### Campaign Creation

```text
Campaign Proposal
      |
      v
Human Approval
      |
      v
Campaign saved
```

### Content Production

```text
Content Plan
      |
      v
Human Approval
      |
      v
status = planned
      |
      v
Content Generation
      |
      v
Human Approval
      |
      v
status = draft
```

This means neither campaign creation nor generated content persistence happens solely because an AI agent decided to perform the action.

---

## Current Content Lifecycle

Implemented:

```text
                 Human approval
                       |
                       v
Content Plan ------> planned
                       |
                       | Content Generation
                       v
                Generated Proposal
                       |
                       | Human approval
                       v
                     draft
```

Planned:

```text
draft
  |
  v
Review Agent
  |
  v
review / approved
  |
  v
scheduling
  |
  v
published
```

---

## Next Development Milestone

The next planned specialist is the:

```text
Review Agent
```

Its role will be different from the Content Generation Agent.

The generator asks:

```text
How should this post be written?
```

The Review Agent will eventually ask:

```text
Should this draft be allowed to progress?
```

Potential review responsibilities include:

- checking factual grounding;
- checking alignment with the campaign;
- checking platform suitability;
- identifying unsupported claims;
- checking whether required brand information is missing;
- identifying obvious quality problems; and
- recommending approval, revision, or rejection.

The Review Agent will first be implemented as a read-only reviewer before any additional state transition is introduced.

## Review Agent

The next specialist added to the multi-agent architecture is the **Review Agent**.

Its responsibility is different from the Content Planning Agent and Content Generation Agent:

```text
Content Planning Agent
→ Decides WHAT content should be created.

Content Generation Agent
→ Decides HOW approved planned content should be written.

Review Agent
→ Determines whether generated draft content is suitable to progress.
```

The Review Agent is currently implemented as a **read-only specialist**.

It does not have permission to:

* modify content;
* save revised content;
* change content status;
* approve content directly in ClickHouse;
* schedule or publish content.

This maintains the system's human-in-the-loop architecture, where specialist agents reason and recommend while consequential persistent actions remain controlled by the root orchestrator.

### Review Agent Architecture

The current multi-agent architecture is:

```text
                     User
                      |
                      v
             Social Media Producer
                / Orchestrator
                      |
        +-------------+-------------+
        |             |             |
        v             v             v
 Content Planning   Content       Review
      Agent        Generation      Agent
                     Agent
        |             |             |
        v             v             v
   Plan Content   Generate Copy   Assess Draft
                                      |
                                      v
                           PASS / REVISE / BLOCKED
```

The Review Agent retrieves a specific content item through a guarded read tool.

```text
Content ID
   ↓
get_draft_content_item()
   ↓
Content must exist
   ↓
Content must have status = draft
   ↓
Review Agent
   ↓
PASS / REVISE / BLOCKED
```

No ClickHouse mutation occurs during this process.

### Review Criteria

The Review Agent currently evaluates draft content for:

* factual grounding;
* campaign alignment;
* content-purpose alignment;
* platform suitability;
* unsupported claims;
* missing information;
* obvious quality problems.

The agent returns one of three recommendations:

```text
PASS
REVISE
BLOCKED
```

A recommendation does not itself change the content item's status.

### Successful Review Test — Content ID 4

Content ID 4 was used for the first real orchestrated review test.

The item contained Facebook engagement copy asking technology learners which practical IT skill they would most like to learn.

The Review Agent returned:

```text
Recommendation: PASS

Reason:
The content aligns with the intended engagement purpose,
is suitable for Facebook, and contains no unsupported
factual claims or statistics.

Issues:
None

Suggested changes:
None
```

After the review, ClickHouse was independently queried.

Content ID 4 remained:

```text
status = draft
```

and its `content_text` remained unchanged.

This demonstrated:

```text
Root Orchestrator
      ↓
Review Agent
      ↓
Draft Retrieval
      ↓
Review
      ↓
PASS
      ↓
No Database Mutation
```

The read-only boundary therefore worked as intended.

### Negative Grounding Test

A deliberately problematic draft was created as Content ID 6.

```text
Content ID: 6
Campaign ID: 2
Platform: Facebook
Content Type: promotional
Topic: BePlugged Tech learner success
Campaign Day: 5
Status: draft
```

The test copy intentionally contains unsupported claims:

```text
BePlugged Tech has helped over 10,000 South African learners
secure high-paying IT jobs. Join our training today and become
our next success story!
```

Neither the claim of helping more than 10,000 learners nor the employment outcome is supported by the currently stored brand information.

The purpose of this test is to verify that the Review Agent detects unsupported numerical, business, and outcome claims rather than allowing them to progress.

### Wrong-Content Review Discovered During Testing

During the first attempt at the negative test, the Review Agent returned a review for a different content item.

The response described:

* an educational Facebook post;
* a single short sentence;
* an empty `content_purpose`;
* insufficient educational depth.

Database inspection showed that these characteristics corresponded to Content ID 1 rather than the intended Content ID 6.

The database was then inspected directly using `get_content_items(2)`, confirming that Content ID 6 existed with the intended deliberately unsupported promotional claims.

This highlighted an important orchestration requirement:

```text
Requested Content ID
        ↓
Root Orchestrator
        ↓
Correct Specialist
        ↓
Exact Requested Record
```

A plausible review is not sufficient. The system must demonstrate that the specialist reviewed the exact requested database record.

Future tests should therefore explicitly verify content identity as well as review quality.

### Gemini Quota Failure During Negative Test

The corrected Content ID 6 test was then attempted with an explicit instruction to retrieve and review that exact record.

Gemini returned:

```text
429 RESOURCE_EXHAUSTED
```

The error reported that the free-tier request quota for the configured Gemini model had been exceeded.

The reported quota was:

```text
generate_content_free_tier_requests
limit: 20
model: gemini-3.5-flash
```

This was an external model quota limitation rather than a ClickHouse, Review Agent, or application architecture failure.

The project has therefore encountered three distinct Gemini/API operational failures during development:

```text
404 NOT_FOUND
→ Model availability/version issue

503 UNAVAILABLE
→ Temporary model/service capacity issue

429 RESOURCE_EXHAUSTED
→ API quota limitation
```

The 429 error is particularly relevant to the multi-agent architecture because one user workflow may require multiple model invocations as work is delegated between specialist agents.

Quota handling, retries, observability, and production model limits should therefore be considered later when the system moves toward deployment.

No architecture redesign is being performed solely because of this development-time quota failure.

### Current Review Agent Test Status

The following has been proven:

```text
[✓] Review Agent created
[✓] Review Agent imports successfully
[✓] Review Agent connected to root orchestrator
[✓] Root agent recognises three specialist agents
[✓] Draft-only guarded retrieval
[✓] Successful Content ID 4 review
[✓] PASS recommendation
[✓] Read-only Review Agent behaviour
[✓] No ClickHouse mutation after review
[✓] Independent database verification
[✓] Wrong-content orchestration issue identified
[✓] Negative test record created as Content ID 6
[✓] Gemini 429 quota failure identified

[ ] Content ID 6 unsupported-claim detection test completed
[ ] REVISE/BLOCKED behaviour independently verified
[ ] Controlled draft → approved transition
```

The negative Content ID 6 test remains **incomplete** because Gemini quota exhaustion prevented the corrected review request from completing.

The next test after quota availability is restored is:

```text
Content ID 6
    ↓
Review Agent
    ↓
Detect unsupported claims
    ↓
REVISE or BLOCKED
    ↓
Verify ClickHouse
    ↓
Content must remain draft
```

Only after the Review Agent's negative behaviour has been proven should a controlled `draft → approved` workflow be considered.

## Review Agent — Completed Milestone

The third specialist added to the AI Social Media Producer is the **Review Agent**.

Its responsibility is:

> Determine whether generated draft content is suitable to progress.

The Review Agent is deliberately **read-only**.

It can inspect draft content and recommend an outcome, but it cannot:

* modify content;
* save revised content;
* change content status;
* approve content directly;
* schedule content;
* publish content;
* perform ClickHouse mutations.

This preserves the project's human-in-the-loop architecture.

### Agent Responsibility Separation

The implemented specialist responsibilities are now:

```text
Content Planning Agent
→ Decides WHAT content should be created.

Content Generation Agent
→ Decides HOW approved planned content should be written.

Review Agent
→ Determines whether generated draft content is suitable to progress.
```

The root Social Media Producer remains responsible for orchestration and consequential persistent actions.

### Current Multi-Agent Architecture

```text
                       User
                        |
                        v
              Social Media Producer
                 / Orchestrator
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
     Content        Content         Review
     Planning      Generation       Agent
      Agent          Agent
          |             |             |
          v             v             v
    Plan Content   Generate Copy   Assess Draft
                                      |
                                      v
                           PASS / REVISE / BLOCKED
                                      |
                                      v
                              Human Decision
```

The Review Agent does not convert a recommendation into a database state change.

### Guarded Draft Retrieval

The Review Agent uses:

```text
get_draft_content_item()
```

to retrieve the requested content.

The tool verifies:

1. the content item exists;
2. the requested record is retrieved;
3. the item has `status = draft`.

Conceptually:

```text
Content ID
    ↓
get_draft_content_item()
    ↓
Content exists?
    ↓
status == draft?
    ↓
Review Agent
    ↓
PASS / REVISE / BLOCKED
```

No write tool is available to the Review Agent.

---

## Review Criteria

The Review Agent evaluates content for:

* factual grounding;
* unsupported claims;
* campaign alignment;
* content-purpose alignment;
* brand alignment;
* platform suitability;
* missing information;
* obvious quality problems.

The Review Agent returns one of three recommendations:

```text
PASS
REVISE
BLOCKED
```

A recommendation is advisory only.

`PASS` does not automatically mean:

```text
status = approved
```

Similarly, `BLOCKED` does not automatically modify or delete the draft.

---

## Positive Review Test — Content ID 4

Content ID 4 was used to test the normal successful review path.

The content was:

```text
Platform: Facebook
Type: engagement
Campaign Day: 4
Topic: Which IT skill would you most like to learn?
Status: draft
```

The draft asked technology learners which practical IT skill they would most like to master.

The Review Agent returned:

```text
Recommendation: PASS
```

It determined that:

* the copy aligned with the intended engagement purpose;
* the tone was appropriate for Facebook;
* the content contained no unsupported statistics;
* the content contained no unsupported factual claims.

It returned:

```text
Issues: None

Suggested changes: None
```

### Independent Database Verification

After the review, Content ID 4 was independently retrieved from ClickHouse.

It remained:

```text
status = draft
```

and its `content_text` was unchanged.

This proved:

```text
Root Orchestrator
      ↓
Review Agent
      ↓
Content ID 4
      ↓
PASS
      ↓
NO DATABASE MUTATION
      ↓
status remains draft
```

---

# Negative Grounding Test — Content ID 6

A deliberately problematic draft was created to test whether the Review Agent would detect unsupported factual claims rather than simply approve plausible-looking social-media copy.

Content ID 6 contained:

```text
Content ID: 6
Campaign ID: 2
Platform: Facebook
Content Type: promotional
Topic: BePlugged Tech learner success
Campaign Day: 5
Status: draft
```

The deliberately problematic copy was:

```text
BePlugged Tech has helped over 10,000 South African learners
secure high-paying IT jobs. Join our training today and become
our next success story!
```

Two important claims were intentionally unsupported:

```text
"over 10,000 South African learners"

"secure high-paying IT jobs"
```

Neither claim was supported by the available brand or campaign information.

---

## Exact-Record Retrieval Issue Discovered

The first attempt at the negative test produced a review describing an educational Facebook post with:

* one short sentence;
* an empty `content_purpose`;
* insufficient educational depth.

Database inspection showed that these characteristics corresponded to **Content ID 1**, not Content ID 6.

The database was inspected directly using:

```text
get_content_items(2)
```

This confirmed that Content ID 6 existed and contained the deliberately unsupported promotional claims.

The test request was then strengthened to explicitly require:

```text
Review Content ID 6.

Use the Review Agent to retrieve Content ID 6 from ClickHouse
and review that exact draft.

Do not review any other content item.
```

This development issue highlighted an important orchestration requirement:

```text
Correct Specialist
        +
Correct Database Record
        =
Valid Agent Result
```

A plausible AI response is not sufficient evidence of correct orchestration.

---

# Successful BLOCKED Test

When the corrected Content ID 6 test was executed, the Review Agent returned:

```text
Recommendation: BLOCKED
```

The reason was that the draft contained highly specific statistical and factual claims that could not be verified using the available campaign or brand context.

The Review Agent specifically detected:

```text
"over 10,000 South African learners"
```

and:

```text
"high-paying IT jobs"
```

as unsupported claims.

This successfully demonstrated that the Review Agent does not merely evaluate writing quality.

It can identify when apparently persuasive marketing copy depends on information that has not been grounded in available evidence.

The resulting flow was:

```text
Content ID 6
      ↓
Root Orchestrator
      ↓
Review Agent
      ↓
Exact Draft Retrieved
      ↓
Factual Grounding Check
      ↓
Unsupported Claims Detected
      ↓
BLOCKED
```

---

## Independent Safety Verification

After the `BLOCKED` recommendation, Content ID 6 was independently queried from ClickHouse.

The database still contained:

```text
content_id = 6
status = draft
```

The original `content_text` was also completely unchanged.

Therefore:

```text
BLOCKED
   ≠
Database Mutation
```

The Review Agent detected the problem but did not modify the underlying content.

This independently proves the intended read-only safety boundary:

```text
Review Agent
      ↓
Reason
      ↓
Recommend
      ↓
STOP

Human / Orchestrator remains responsible
for consequential state changes.
```

---

# Grounding Weakness Discovered in Suggested Changes

The negative test revealed an additional grounding issue.

Although the Review Agent correctly returned `BLOCKED`, one of its suggested safer alternatives included wording similar to:

```text
BePlugged Tech has helped South African learners
launch their careers in IT.
```

This removes the unsupported numerical claim but still introduces an unsupported learner-outcome claim.

The Review Agent therefore made the correct **classification decision**, but its suggested replacement copy was not fully grounded.

This leads to an additional design principle:

```text
GROUNDING MUST APPLY TO:

Original content
        AND
Review reasoning
        AND
Suggested revisions
```

A Review Agent must not remove one unsupported claim by replacing it with another unsupported claim.

Future Review Agent instructions should explicitly require suggested changes and example rewrites to follow the same grounding rules as the content being reviewed.

This is a known improvement rather than evidence that the `BLOCKED` classification failed.

---

# Gemini Quota Failure During Testing

The negative test was temporarily interrupted by:

```text
429 RESOURCE_EXHAUSTED
```

Gemini reported that the configured free-tier request quota had been exceeded.

The reported quota included:

```text
generate_content_free_tier_requests
limit: 20
model: gemini-3.5-flash
```

This was an external model quota limitation rather than a ClickHouse or application architecture failure.

Development has now encountered three different external Gemini operational failures:

```text
404 NOT_FOUND
→ Model availability/version problem

503 UNAVAILABLE
→ Temporary service/model capacity problem

429 RESOURCE_EXHAUSTED
→ API quota limitation
```

The 429 failure is particularly relevant to a multi-agent architecture because a single user workflow may involve multiple model calls across the orchestrator and specialist agents.

Production architecture should therefore eventually consider:

* quota management;
* retry behaviour;
* failure handling;
* observability;
* model-call monitoring.

No architecture redesign was performed solely because of the development-time quota failure.

---

# Review Agent Milestone — Final Status

The following capabilities have now been demonstrated:

```text
[✓] Review Agent created
[✓] Review Agent imports successfully
[✓] Review Agent connected to root orchestrator
[✓] Three specialist agents registered
[✓] Guarded draft retrieval
[✓] Draft-only review boundary
[✓] Root → Review Agent delegation
[✓] Exact requested content retrieval tested
[✓] PASS path tested with Content ID 4
[✓] BLOCKED path tested with Content ID 6
[✓] Factual-grounding review
[✓] Unsupported numerical claim detection
[✓] Unsupported outcome claim detection
[✓] Read-only review behaviour
[✓] No ClickHouse mutation after PASS
[✓] No ClickHouse mutation after BLOCKED
[✓] Draft status independently verified
[✓] Original content independently verified unchanged
[✓] Wrong-record orchestration issue discovered and investigated
[✓] Suggested-rewrite grounding weakness identified
[✓] Gemini 429 quota limitation documented
```

The Review Agent milestone is therefore considered **functionally complete**.

One known improvement remains:

```text
Strengthen grounding rules for Review Agent
suggested changes / example rewrites.
```

The next major development direction is the transition from the generic AI Social Media Producer test scenario toward **Premiere — AI Studio Producer**, using the existing multi-agent foundation for independent film release campaigns.
