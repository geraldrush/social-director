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

# Premiere — AI Studio Producer Pivot

## Why the Project Is Evolving

The project originally began as an **AI Social Media Producer** and used BePlugged Tech campaigns as the initial development and testing scenario.

That implementation successfully established the core multi-agent architecture:

```text
Root Orchestrator
        |
        +-- Content Planning Agent
        |
        +-- Content Generation Agent
        |
        +-- Review Agent
```

It also established important engineering boundaries including:

* explicit human approval before persistent state changes;
* specialist-agent responsibility separation;
* grounded content generation;
* guarded database retrieval;
* read-only content review;
* ClickHouse persistence;
* independent database verification.

The project is now evolving into:

> **Premiere — AI Studio Producer**

Premiere applies the existing multi-agent architecture to **independent film release campaigns**.

Rather than rebuilding the system, the film-studio workflow is being introduced incrementally and tested against the existing architecture.

---

# Premiere Product Direction

Premiere is being designed as a multi-agent AI studio producer for independent filmmakers and film studios.

The intended workflow is:

```text
Independent Film Studio
        ↓
Film / Release Brief
        ↓
Director Agent
        ↓
Content Planning
        ↓
Content Generation
        ↓
Content Review
        ↓
Human Approval
        ↓
Publishing Workflow
        ↓
Audience Engagement Events
        ↓
ClickHouse Analytics
        ↓
Analytics Agent
        ↓
Optimisation Agent
```

Only the portions explicitly documented as implemented should be considered current functionality.

Publishing, engagement ingestion, analytics, optimisation, and the complete production architecture remain future milestones unless otherwise documented.

---

# Development Film Scenario

A fictional independent film and studio were introduced as controlled development data.

## Studio

```text
Ubuntu Frame Studios
```

Industry:

```text
Independent film production
```

Target audience:

```text
African film audiences aged 18 to 35
```

Studio tone:

```text
Cinematic, intriguing, authentic and audience-focused
```

## Film

```text
Shadows of Pretoria
```

Verified development facts:

```text
Title:
Shadows of Pretoria

Genre:
Crime drama

Premiere:
20 October 2026

Primary market:
South Africa

Target audience:
African film audiences aged 18 to 35

Release campaign platforms:
Instagram
TikTok
Facebook
YouTube
```

These are fictional development facts used to test grounding behaviour.

The agents must not infer additional film information from these values.

For example:

```text
Film title contains "Pretoria"
        ≠
Film is verified as being set in Pretoria
```

Similarly, no cast, characters, synopsis, filming locations, reviews, awards, trailer assets, behind-the-scenes material, ticket information, venue details, or distribution details should be assumed unless explicitly supplied.

---

# Film / Studio Grounding Rules

The Director Agent was extended with film-specific grounding rules.

When operating on film, studio, entertainment, or release-campaign information, the system must:

* treat only retrieved studio information as verified facts;
* avoid assuming promotional assets exist;
* avoid inventing cast or character information;
* avoid inventing plot information;
* avoid inventing reviews or audience reactions;
* avoid inventing awards;
* avoid inventing quotes;
* avoid inventing filming locations;
* avoid inventing premiere venues;
* avoid inventing distribution information;
* avoid inventing ticket information;
* distinguish recommendations from known facts.

Campaign ideas may recommend content requiring additional studio material, but they must not represent that material as already available.

The grounding rules were further strengthened to prevent inference of:

* plot;
* setting;
* filming location;
* characters;
* themes;
* story events;

from a film title, genre, campaign topic, or other metadata.

---

# First Premiere Campaign

The Director Agent was given the following film-release brief:

```text
Studio:
Ubuntu Frame Studios

Film:
Shadows of Pretoria

Objective:
Build awareness and audience engagement leading up to the premiere.

Target audience:
African film audiences aged 18 to 35.

Platforms:
Instagram, TikTok, Facebook and YouTube.

Duration:
28 days

Premiere:
20 October 2026
```

The Director Agent retrieved the stored studio information and proposed a release campaign.

It correctly stopped before persistence and requested explicit human approval.

This demonstrated that the existing human-in-the-loop campaign creation boundary continued to operate in the film domain.

---

# Grounding Issue Discovered During Campaign Proposal

The first film campaign proposal suggested content involving:

* behind-the-scenes material;
* character reveals;
* plot-based intrigue;
* Pretoria-based atmosphere.

Some of these ideas depended on information or assets that had not been supplied.

The Director Agent grounding rules were therefore strengthened.

After the change, the Director Agent began explicitly distinguishing between:

```text
VERIFIED FILM INFORMATION
```

and:

```text
CONTENT IDEA REQUIRING STUDIO INFORMATION / ASSETS
```

This established an important Premiere design principle:

```text
A good campaign idea
        ≠
Evidence that the required material exists
```

---

# Campaign 3 Created

After human review and explicit approval, the first Premiere campaign was persisted to ClickHouse.

Independent database verification confirmed:

```text
campaign_id = 3

brand_name = Ubuntu Frame Studios

objective =
Build awareness and audience engagement leading up to the premiere.

target_audience =
African film audiences aged 18 to 35

platforms =
Instagram
TikTok
Facebook
YouTube

duration_days = 28

status = draft
```

Only the verified campaign parameters were persisted.

Conditional content ideas were not stored as verified film facts.

---

# Premiere Content Planning Test

Campaign ID 3 was then delegated to the existing **Content Planning Agent**.

The agent was instructed to plan the first seven campaign days while:

* using only verified campaign/studio information;
* avoiding invented film facts;
* identifying ideas requiring unavailable studio information or assets;
* stopping before persistence.

The first planning attempt revealed additional grounding problems.

In particular, the planner inferred that Pretoria was the film's setting based on the film title.

Examples included concepts such as:

```text
Pretoria as a Character
```

and references to the film's supposed Pretoria setting.

This information had never been verified.

---

# Content Planner Grounding Improvement

Film-specific grounding rules were therefore added to the Content Planning Agent.

The planner was instructed not to infer:

* setting;
* filming location;
* plot;
* characters;
* themes;
* cast;
* crew;
* production history;
* reviews;
* awards;
* quotes;
* audience reactions;
* distribution method;
* venue;
* ticket information;
* promotional assets;

from film metadata.

The planner was also instructed to:

* distinguish verified information from missing information;
* mark asset-dependent ideas clearly;
* avoid constructing a content purpose around unsupported assumptions;
* consider dependencies between campaign content items.

The same Campaign 3 planning request was then repeated.

The second plan demonstrated substantially improved grounding behaviour.

It correctly identified several ideas as requiring studio information rather than assuming the required assets existed.

---

# Planning Lessons

The Premiere planning tests established another important distinction:

```text
VERIFIED
```

is different from:

```text
REQUIRES STUDIO INFORMATION
```

and future workflow design may benefit from more expressive states such as:

```text
VERIFIED

REQUIRES STUDIO INFORMATION

REQUIRES STUDIO ASSET

BLOCKED BY DEPENDENCY
```

These states have not yet been implemented as database state transitions.

They are documented as a future design consideration.

---

# Selective Human Approval Test

Rather than approving the complete seven-day plan, only one grounded item was approved.

The approved item was:

```text
Campaign ID:
3

Platform:
Instagram

Content Type:
engagement

Topic:
Interactive Q&A / Premiere Countdown Kickoff

Campaign Day:
5

Content Purpose:
Encourage audience interaction and build excitement
leading up to the verified 20 October 2026 premiere.
```

The root orchestrator was explicitly instructed not to save Days 1, 2, 3, 4, 6, or 7.

The approved item was persisted as:

```text
Content ID 7
```

---

# Independent Planning-State Verification

ClickHouse was queried independently after persistence.

Campaign 3 contained exactly one content item:

```text
content_id = 7
campaign_id = 3
platform = Instagram
content_type = engagement
campaign_day = 5
status = planned
content_text = ""
```

No unapproved planning items were present.

This demonstrated selective human approval:

```text
7 proposed ideas
        ↓
Human approves 1
        ↓
Root Orchestrator
        ↓
Only approved item persisted
        ↓
ClickHouse
        ↓
1 planned item
```

---

# Premiere Content Generation Test

Content ID 7 was then delegated to the existing **Content Generation Agent**.

The Generation Agent was instructed to:

* retrieve the exact content item;
* use its campaign context;
* generate Instagram-specific copy;
* use only verified information;
* avoid inventing film facts;
* stop before persistence.

The first draft correctly used the verified premiere date but contained slightly inaccurate wording describing the event as an:

```text
Ubuntu Frame Studios premiere
```

The verified fact was specifically:

```text
Shadows of Pretoria premieres on 20 October 2026.
```

The draft was therefore not immediately approved.

---

# Human-Guided Revision

The human requested a targeted revision.

The Generation Agent was instructed to:

* preserve the existing concept;
* correct the premiere wording;
* introduce no new film facts;
* stop before persistence.

The revised copy was:

```text
The countdown is officially on! ⏳

Shadows of Pretoria premieres on 20 October 2026.

We want to hear from you: What are you most looking forward
to as we count down to the release, and where are you tuning
in from? Drop your thoughts in the comments below! 👇✨

#ShadowsOfPretoria #UbuntuFrameStudios
#PremiereCountdown #AfricanCinema #FilmCommunity
```

The human explicitly approved this exact revision.

---

# Planned → Draft Transition

After explicit approval, the root orchestrator persisted the exact revised copy.

Independent ClickHouse verification confirmed:

```text
content_id = 7
campaign_id = 3
platform = Instagram
status = draft
```

The stored `content_text` matched the approved revision.

The resulting state transition was:

```text
Content ID 7

planned
   ↓
Generation Agent
   ↓
Generated Draft
   ↓
Human Revision Request
   ↓
Revised Draft
   ↓
Explicit Human Approval
   ↓
Root Orchestrator
   ↓
ClickHouse
   ↓
draft
```

---

# First Premiere Review Test

The persisted Content ID 7 draft was then delegated to the existing **Review Agent**.

The Review Agent was instructed to retrieve the exact ClickHouse record and assess:

* factual grounding;
* campaign alignment;
* content-purpose alignment;
* studio/brand tone;
* Instagram suitability.

The Review Agent returned:

```text
Recommendation: PASS
```

Reason:

```text
The draft is factually accurate according to the verified
campaign details, aligned with the content purpose of driving
audience interaction, and appropriate for Instagram.
```

The Review Agent reported:

```text
Issues: None

Suggested changes: None
```

---

# Review State Verification

After the `PASS` recommendation, Content ID 7 was independently retrieved from ClickHouse.

It remained:

```text
status = draft
```

The approved `content_text` was unchanged.

Therefore:

```text
Review Agent PASS
        ≠
Automatic Approval
```

The Review Agent remained read-only in the Premiere workflow.

---

# First Complete Premiere Multi-Agent Pipeline

The following film-release workflow has now been demonstrated:

```text
Ubuntu Frame Studios
        ↓
Shadows of Pretoria
        ↓
Campaign Brief
        ↓
Director / Root Orchestrator
        ↓
Human Campaign Approval
        ↓
Campaign 3
        ↓
ClickHouse
        ↓
Content Planning Agent
        ↓
7-Day Plan Proposed
        ↓
Human Selective Approval
        ↓
Content ID 7
status = planned
        ↓
Content Generation Agent
        ↓
Draft Generated
        ↓
Human Revision Request
        ↓
Draft Revised
        ↓
Explicit Human Approval
        ↓
Content ID 7
status = draft
        ↓
Review Agent
        ↓
PASS
        ↓
Independent ClickHouse Verification
        ↓
Content ID 7 remains draft
```

This is the first complete demonstration that the existing multi-agent architecture can operate on an independent-film release workflow rather than only the original generic business-marketing scenario.

---

# Premiere Milestone Status

The following has now been demonstrated:

```text
[✓] Fictional studio development context created
[✓] Fictional film development context created
[✓] Verified film facts explicitly defined
[✓] Film/studio grounding rules introduced
[✓] Director Agent grounding tested
[✓] Unsupported setting inference discovered
[✓] Director grounding rules strengthened
[✓] First film-release campaign proposed
[✓] Human campaign approval enforced
[✓] Campaign 3 persisted to ClickHouse
[✓] Film-release Content Planning Agent test
[✓] Planner grounding weaknesses discovered
[✓] Film-specific planner rules introduced
[✓] Improved planning behaviour demonstrated
[✓] Selective plan approval demonstrated
[✓] Only approved content persisted
[✓] Content ID 7 created as planned
[✓] Content Generation Agent used in film workflow
[✓] Human-guided content revision demonstrated
[✓] Exact approved copy persisted
[✓] planned → draft transition verified
[✓] Review Agent used in film workflow
[✓] Review Agent returned PASS
[✓] Review Agent remained read-only
[✓] Content remained draft after PASS
[✓] First complete Premiere specialist pipeline demonstrated
```

---

# Known Improvements

The Premiere testing process has revealed several improvements that should be addressed incrementally.

## 1. Review Suggested-Rewrite Grounding

The earlier Review Agent negative test demonstrated that a correct `BLOCKED` classification can still be followed by a suggested rewrite containing a weaker unsupported claim.

Grounding rules should therefore explicitly apply to:

```text
Original content
+
Review reasoning
+
Suggested revisions
```

## 2. More Expressive Content Dependencies

Film-release planning may eventually distinguish between:

```text
VERIFIED
REQUIRES STUDIO INFORMATION
REQUIRES STUDIO ASSET
BLOCKED BY DEPENDENCY
```

This has not yet been implemented.

## 3. Campaign Timing

The campaign currently stores `duration_days`, but the workflow does not yet have a complete release-campaign scheduling model.

Exact countdown calculations should not be inferred without sufficient scheduling information.

## 4. Film Domain Model

The current campaign structure successfully supports the initial Premiere test.

A dedicated film-domain model may later include information such as:

```text
films
release information
approved studio facts
approved promotional assets
rating / audience constraints
```

The schema should only be expanded when required by tested functionality.

---

# Next Technical Milestones

The immediate technical direction after the first successful Premiere pipeline is:

```text
Completed Premiere Pipeline
        ↓
Strengthen Review Agent rewrite grounding
        ↓
Official ClickHouse MCP Integration
        ↓
Prove Runtime MCP Query
        ↓
Agent Execution Observability
        ↓
agent_events
        ↓
Audience Engagement Event Model
        ↓
engagement_events
        ↓
ClickHouse Materialized Views
        ↓
Analytics Agent
        ↓
Optimisation Agent
        ↓
Google Cloud Production Deployment
```

The project will continue following the same development discipline:

```text
Build
  ↓
Test
  ↓
Find Boundary Failures
  ↓
Improve
  ↓
Retest
  ↓
Verify ClickHouse State
  ↓
Document
  ↓
Commit
```

The project should not claim future functionality as implemented until it has been tested and independently verified.

# Official ClickHouse MCP Integration

## Objective

Premiere already uses ClickHouse directly through the Python `clickhouse-connect` client in `database.py`.

The next integration milestone was to prove that the same application data could be accessed through the **official ClickHouse MCP server (`mcp-clickhouse`)**.

The existing direct database integration was intentionally retained while MCP was introduced alongside it.

The initial architecture is therefore:

```text
                    Premiere
                       |
          +------------+------------+
          |                         |
          v                         v
     database.py              MCP Integration
          |                         |
          v                         v
 clickhouse-connect          mcp-clickhouse
          |                         |
          +------------+------------+
                       |
                       v
                   ClickHouse
                       |
              social_producer
```

This incremental approach avoids replacing a proven database integration before the MCP path has been independently tested.

---

# Local Development Environment

The first MCP integration was developed against the existing local ClickHouse Docker instance.

ClickHouse was reachable through its HTTP interface at:

```text
localhost:8123
```

Authenticated HTTP connectivity was verified with:

```bash
curl -u "social_producer:<password>" \
  "http://localhost:8123/?query=SELECT%20version()"
```

The server returned:

```text
26.7.4.58
```

This confirmed:

```text
ClickHouse Docker
        ↓
HTTP :8123
        ↓
Authentication
        ↓
ClickHouse 26.7.4.58
```

Secrets are stored locally and are not committed to the repository.

---

# uv Installation

The `uv` package manager was installed in the WSL development environment.

Verified version:

```text
uv 0.12.5
```

This was used to run the official ClickHouse MCP server without modifying the existing project dependency environment.

---

# MCP Connection Configuration

The MCP server was configured against the existing local ClickHouse instance using environment variables.

The development configuration used:

```text
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=social_producer
CLICKHOUSE_DATABASE=social_producer
CLICKHOUSE_SECURE=false
CLICKHOUSE_VERIFY=false
CLICKHOUSE_ALLOW_WRITE_ACCESS=false
```

`CLICKHOUSE_PASSWORD` was supplied locally and is intentionally omitted from documentation.

Write access was explicitly disabled during the first MCP integration tests.

Therefore the initial MCP boundary was:

```text
mcp-clickhouse
      ↓
READ ONLY
      ↓
social_producer
```

This prevents the first MCP integration from modifying campaign or content state.

---

# Official MCP Server Startup

The ClickHouse MCP server was started using:

```bash
uv run --with mcp-clickhouse --python 3.10 mcp-clickhouse
```

The server successfully reported:

```text
ClickHouse tools registered
```

and:

```text
Starting MCP server 'mcp-clickhouse'
```

The initial transport was:

```text
stdio
```

This confirmed that the official MCP server could start successfully with the local ClickHouse configuration.

---

# HTTP MCP Transport

For easier local integration testing, the server was then configured to use HTTP transport.

Development-only MCP authentication was disabled for the local test environment.

The server successfully started at:

```text
http://127.0.0.1:8000/mcp
```

Uvicorn reported successful application startup.

The local architecture became:

```text
MCP Client
    |
    | HTTP
    v
127.0.0.1:8000/mcp
    |
    v
mcp-clickhouse
    |
    | ClickHouse HTTP
    v
localhost:8123
    |
    v
ClickHouse
```

Authentication being disabled at the MCP HTTP layer is strictly a local-development configuration and is not intended for production deployment.

ClickHouse itself remained authenticated.

---

# MCP Protocol Verification

A basic HTTP request was sent to the MCP endpoint.

The server returned an MCP protocol response indicating that the client needed to support:

```text
text/event-stream
```

This demonstrated that:

```text
HTTP endpoint reachable          ✓
MCP server responding            ✓
MCP protocol active              ✓
```

The plain HTTP request was not treated as a normal REST request, which is expected for an MCP protocol endpoint.

---

# MCP Tool Discovery

An MCP-aware FastMCP client was then used to inspect the running server.

The official ClickHouse MCP server exposed three tools:

```text
list_databases
list_tables
run_query
```

## `list_databases`

Purpose:

```text
List available ClickHouse databases.
```

## `list_tables`

Purpose:

```text
Inspect tables within a ClickHouse database,
including schema and storage information.
```

## `run_query`

Purpose:

```text
Execute ClickHouse SQL queries.
```

The tool reported that queries operate in read-only mode by default unless write access is explicitly enabled.

This matched the intended security boundary for the first Premiere MCP integration.

---

# MCP Database Discovery Test

The `list_databases` MCP tool was executed against the running server.

The returned databases included:

```text
INFORMATION_SCHEMA
default
information_schema
social_producer
system
```

The important result was:

```text
social_producer
```

This proved that the official MCP server could successfully authenticate with ClickHouse and discover the Premiere development database.

The verified path was:

```text
FastMCP Client
      ↓
mcp-clickhouse
      ↓
ClickHouse
      ↓
social_producer
```

---

# MCP Table Discovery Test

The `list_tables` tool was then executed against:

```text
social_producer
```

The MCP server returned:

```text
campaigns
content_items
```

It also returned the actual ClickHouse metadata for both tables.

## Campaigns

Verified storage engine:

```text
MergeTree
```

Verified sorting key:

```text
brand_name, campaign_id
```

At the time of the MCP test:

```text
total_rows = 3
```

## Content Items

Verified storage engine:

```text
MergeTree
```

Verified sorting key:

```text
campaign_id, platform, content_id
```

At the time of the MCP test:

```text
total_rows = 7
```

This demonstrated that MCP could inspect the actual schema rather than merely establish a network connection.

---

# Premiere Campaign Query Through MCP

The `run_query` MCP tool was used to retrieve Campaign ID 3.

The query targeted:

```text
social_producer.campaigns
```

with:

```text
campaign_id = 3
```

MCP returned:

```text
campaign_id:
3

brand_name:
Ubuntu Frame Studios

objective:
Build awareness and audience engagement leading up to the premiere.

target_audience:
African film audiences aged 18 to 35

platforms:
Instagram
TikTok
Facebook
YouTube

duration_days:
28

status:
draft
```

This was the same Premiere campaign previously created through the existing agent workflow and persisted through the direct ClickHouse integration.

Therefore:

```text
Campaign 3
     ↓
ClickHouse
     ↓
mcp-clickhouse
     ↓
run_query
     ↓
Campaign successfully retrieved
```

---

# Premiere Content Query Through MCP

The MCP `run_query` tool was then used to retrieve:

```text
Content ID 7
```

from:

```text
social_producer.content_items
```

The MCP result confirmed:

```text
content_id:
7

campaign_id:
3

platform:
Instagram

content_type:
engagement

topic:
Interactive Q&A / Premiere Countdown Kickoff

campaign_day:
5

content_purpose:
Encourage audience interaction and build excitement
leading up to the verified 20 October 2026 premiere.

status:
draft
```

The persisted copy retrieved through MCP was:

```text
The countdown is officially on! ⏳

Shadows of Pretoria premieres on 20 October 2026.

We want to hear from you: What are you most looking forward
to as we count down to the release, and where are you tuning
in from? Drop your thoughts in the comments below! 👇✨

#ShadowsOfPretoria #UbuntuFrameStudios
#PremiereCountdown #AfricanCinema #FilmCommunity
```

This matched the exact human-approved Premiere draft previously verified through `database.py`.

---

# Dual ClickHouse Access Paths Proven

Premiere now has two independently tested paths to the same ClickHouse state.

## Existing Direct Integration

```text
Premiere
    ↓
database.py
    ↓
clickhouse-connect
    ↓
ClickHouse
```

This path currently handles the application's proven persistence workflow.

## Official MCP Integration

```text
MCP Client
    ↓
Official mcp-clickhouse
    ↓
ClickHouse
```

This path has successfully demonstrated:

```text
Database discovery    ✓
Table discovery       ✓
Schema inspection     ✓
Campaign queries      ✓
Content queries       ✓
Read-only boundary    ✓
```

Both paths independently retrieved the same Premiere application state.

---

# Why Direct Integration Has Not Been Removed

The existing `database.py` implementation remains intentionally intact.

The MCP milestone was introduced incrementally rather than immediately replacing working persistence code.

Current state:

```text
database.py
    ↓
Proven application persistence

mcp-clickhouse
    ↓
Proven MCP discovery/query integration
```

The next milestone will determine which agent operations should use MCP directly.

This prevents architectural changes from being made merely for demonstration purposes without first verifying their runtime behaviour.

---

# Current MCP Security Boundary

During this development milestone:

```text
CLICKHOUSE_ALLOW_WRITE_ACCESS=false
```

Therefore the MCP server is being treated as a read-only interface.

MCP currently cannot be used by the Premiere workflow to:

```text
INSERT campaign data
UPDATE content state
DELETE records
DROP tables
TRUNCATE tables
```

Existing controlled writes continue through the root orchestrator and the established application tools.

This preserves the existing human-in-the-loop write boundary while MCP integration is introduced.

---

# MCP Milestone Status

The following has now been demonstrated:

```text
[✓] uv installed in WSL
[✓] Local ClickHouse HTTP interface verified
[✓] Authenticated ClickHouse connection verified
[✓] Official mcp-clickhouse server started
[✓] ClickHouse MCP tools registered
[✓] stdio transport verified
[✓] HTTP MCP transport verified
[✓] MCP endpoint reachable
[✓] MCP-aware client connected
[✓] list_databases discovered
[✓] list_tables discovered
[✓] run_query discovered
[✓] social_producer database discovered through MCP
[✓] campaigns table inspected through MCP
[✓] content_items table inspected through MCP
[✓] MergeTree metadata returned through MCP
[✓] Campaign 3 queried through MCP
[✓] Content ID 7 queried through MCP
[✓] MCP data matched existing application state
[✓] MCP kept read-only during initial integration
```

---

# Important Current Limitation

Although the official MCP server can now successfully query Premiere's ClickHouse data, the current test client is a standalone MCP client.

The following path has been proven:

```text
Human
   ↓
FastMCP Client
   ↓
mcp-clickhouse
   ↓
ClickHouse
```

The following path is the **next milestone** and must not yet be described as implemented:

```text
User
   ↓
Gemini / ADK Agent
   ↓
MCP Tool Call
   ↓
mcp-clickhouse
   ↓
ClickHouse
```

The next task is therefore to connect one Premiere ADK agent to the running MCP server and demonstrate an actual model-initiated ClickHouse MCP tool call.

---

# Next MCP Milestone

The immediate target is:

```text
User:
"What is Campaign 3?"
        ↓
Premiere ADK Agent
        ↓
MCP tool selection
        ↓
run_query
        ↓
mcp-clickhouse
        ↓
ClickHouse
        ↓
Campaign 3
        ↓
Agent response
```

The initial ADK integration should remain read-only.

Only after agent-driven MCP reads have been demonstrated and tested should MCP write access be considered.

The project will continue to follow:

```text
Build
  ↓
Test
  ↓
Verify
  ↓
Document
  ↓
Commit
```


# ADK Agent → ClickHouse MCP Runtime Integration

## Objective

The previous MCP milestone proved that the official `mcp-clickhouse` server could independently access Premiere's ClickHouse data.

The next goal was to prove the complete agent-driven runtime path:

```text
User
  ↓
Gemini / Google ADK Agent
  ↓
ADK MCPToolset
  ↓
Official mcp-clickhouse
  ↓
ClickHouse
  ↓
Premiere Data
```

This is materially different from manually invoking MCP tools through a CLI client.

The objective was to demonstrate that a Gemini-powered ADK agent could discover and invoke the official ClickHouse MCP tools itself.

---

# ADK MCP Dependency

The project currently uses:

```text
google-adk == 2.7.1
```

The ADK MCP integration requires the Python `mcp` package.

An initial installation resulted in:

```text
mcp == 2.0.0
```

This was incompatible with the installed ADK version.

ADK expected modules from the MCP 1.x API and produced:

```text
ModuleNotFoundError:
No module named 'mcp.shared.session'
```

The installed ADK package metadata was inspected directly.

It declared:

```text
mcp >= 1.24, < 2
```

The MCP dependency was therefore corrected to:

```text
mcp == 1.29.0
```

After this change:

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
```

imported successfully.

This demonstrated the importance of checking package compatibility rather than simply installing the newest available dependency.

---

# Initial HTTP MCP Attempt

The first ADK integration attempted to connect to the already-running HTTP MCP endpoint:

```text
http://127.0.0.1:8000/mcp
```

The official MCP server itself had already been independently verified using FastMCP.

However, ADK's MCP tool discovery timed out while attempting to create the HTTP MCP session.

The failure occurred during:

```text
list_tools
```

and resulted in:

```text
ConnectionError:
Failed to get tools from MCP server
```

The same MCP HTTP endpoint continued to work correctly with the standalone FastMCP client.

Therefore the failure was isolated to the ADK HTTP MCP session path rather than ClickHouse or `mcp-clickhouse`.

---

# Stdio MCP Integration

Instead of continuing to debug the local HTTP transport, the ADK integration was changed to use MCP's stdio transport.

The ADK `McpToolset` launches the official ClickHouse MCP server as a child process.

Conceptually:

```text
Google ADK Agent
      ↓
McpToolset
      ↓
stdio
      ↓
uv
      ↓
official mcp-clickhouse
      ↓
ClickHouse
```

The ClickHouse MCP server inherited the existing authenticated ClickHouse configuration.

Write access remained disabled:

```text
CLICKHOUSE_ALLOW_WRITE_ACCESS=false
```

Therefore the first ADK-driven MCP integration remained read-only.

---

# MCP Startup Timeout Discovered

The first stdio tool-discovery attempt timed out after 30 seconds.

During the failure, `uv` was still resolving/installing dependencies for the temporary `mcp-clickhouse` runtime environment.

The ADK session timed out before the MCP process became ready.

The MCP session timeout was increased to:

```text
120 seconds
```

and the exact `uv` command was run manually once to warm the dependency cache.

After that, MCP startup completed normally.

This failure was therefore caused by development-time dependency startup latency rather than a protocol or ClickHouse failure.

---

# ADK MCP Tool Discovery

The ADK MCP toolset was tested directly before involving Gemini.

The MCP server processed:

```text
ListToolsRequest
```

and ADK discovered exactly three ClickHouse tools:

```text
Tool count: 3

list_databases
list_tables
run_query
```

This successfully proved:

```text
Google ADK
    ↓
MCPToolset
    ↓
Official mcp-clickhouse
    ↓
Tool discovery
```

The official ClickHouse MCP tools were now visible to the ADK runtime.

---

# Temporary MCP Test Agent

A deliberately isolated test agent was created before modifying the production Premiere orchestrator.

Its responsibility was only to:

* query the `social_producer` database;
* use ClickHouse MCP tools;
* remain read-only;
* avoid inventing database contents.

The test agent had access only to:

```text
list_databases
list_tables
run_query
```

This followed the same development philosophy used for the other Premiere specialists:

```text
Build isolated capability
        ↓
Verify tools
        ↓
Test runtime behaviour
        ↓
Only then integrate with orchestrator
```

---

# Tool Naming Failure

During an early test, Gemini attempted to invoke:

```text
clickhouse__show_tables
```

which was not a registered MCP tool.

ADK correctly rejected the call.

Further investigation showed that MCP tool discovery had not completed successfully in the previous HTTP configuration.

After moving to stdio and successfully discovering the actual tools, the test agent instructions were made explicit:

```text
Available tools:

list_databases
list_tables
run_query
```

The agent was also instructed not to invent tool names.

This reinforced an important rule:

```text
Plausible tool call
        ≠
Registered tool call
```

Agent tool availability must be verified independently.

---

# First Gemini-Initiated ClickHouse MCP Query

The temporary MCP test agent was then run through ADK Web.

The user asked:

```text
What is Campaign ID 3?

Use the ClickHouse MCP tools to query the social_producer database.
Do not answer from memory or assumptions.
```

Gemini successfully used the ClickHouse MCP integration and returned actual Premiere data.

The response included:

```text
Campaign ID:
3

Brand:
Ubuntu Frame Studios

Objective:
Build awareness and audience engagement leading up to the premiere.

Target Audience:
African film audiences aged 18 to 35

Platforms:
Instagram
TikTok
Facebook
YouTube

Duration:
28 days

Status:
Draft
```

The response also retrieved the associated Premiere content item:

```text
Content ID:
7

Platform:
Instagram

Content Type:
Engagement

Topic:
Interactive Q&A / Premiere Countdown Kickoff

Campaign Day:
5

Status:
Draft
```

The data matched the previously verified ClickHouse state.

---

# First Complete Agent-Driven MCP Path

The following runtime path has now been demonstrated:

```text
User
  ↓
Gemini
  ↓
Google ADK Agent
  ↓
McpToolset
  ↓
run_query
  ↓
Official mcp-clickhouse
  ↓
ClickHouse
  ↓
social_producer.campaigns
  ↓
social_producer.content_items
  ↓
Campaign 3 + Content ID 7
  ↓
Gemini Response
```

This is the first successful proof that Gemini itself can access Premiere's ClickHouse state through the official ClickHouse MCP server.

---

# MCP Integration Status

The following is now proven:

```text
[✓] google-adk MCP support identified
[✓] Correct MCP package compatibility established
[✓] mcp 2.x incompatibility identified
[✓] mcp 1.29.0 installed
[✓] MCPToolset imports successfully
[✓] HTTP MCP ADK timeout investigated
[✓] stdio MCP transport configured
[✓] Official mcp-clickhouse launched by ADK
[✓] MCP startup latency issue identified
[✓] MCP session timeout adjusted
[✓] MCP tool discovery verified
[✓] list_databases visible to ADK
[✓] list_tables visible to ADK
[✓] run_query visible to ADK
[✓] Temporary MCP test agent created
[✓] Hallucinated tool-name failure identified
[✓] Gemini initiated an MCP database query
[✓] Campaign 3 retrieved through agent-driven MCP
[✓] Content ID 7 retrieved through agent-driven MCP
[✓] Returned data matched verified ClickHouse state
[✓] MCP remained read-only
```

---

# Important Architecture Boundary

The temporary MCP test agent is not the final Premiere architecture.

Current proven state:

```text
Premiere Root Agent
    ↓
Existing Python database tools
    ↓
clickhouse-connect
```

and separately:

```text
Temporary MCP Test Agent
    ↓
Official mcp-clickhouse
    ↓
ClickHouse
```

The next milestone is to connect controlled read-only MCP access to the actual Premiere orchestration layer.

The temporary test agent should not become a permanent duplicate architecture.

---

# Next Milestone

The next target is:

```text
User
  ↓
Premiere Director Agent
  ↓
Read-only ClickHouse MCP
  ↓
Campaign / Content / Analytics Queries
```

Important database writes should continue to respect explicit human approval.

The initial Director MCP integration should therefore remain:

```text
READ ONLY
```

while controlled state-changing operations continue through the existing orchestrator tools.

Only after this architecture is proven should MCP write access be evaluated.


# Premiere Director Agent → ClickHouse MCP Runtime Integration

## Objective

The official ClickHouse MCP integration had already been proven independently through:

```text
FastMCP Client
    ↓
Official mcp-clickhouse
    ↓
ClickHouse
```

and through a temporary ADK MCP test agent.

The next objective was to integrate the same read-only MCP capability into the actual Premiere root orchestrator.

The target runtime path was:

```text
User
  ↓
Premiere Director / Root Agent
  ↓
Google ADK McpToolset
  ↓
Official mcp-clickhouse
  ↓
ClickHouse
```

---

# Reusable ClickHouse MCP Module

A reusable module was introduced:

```text
social_producer/clickhouse_mcp.py
```

Its responsibility is to configure the official ClickHouse MCP server for the Premiere application.

The MCP server is launched by ADK using stdio rather than requiring a separately running HTTP process.

Conceptually:

```text
Premiere Director
      ↓
clickhouse_mcp.py
      ↓
ADK McpToolset
      ↓
stdio
      ↓
uv
      ↓
official mcp-clickhouse
      ↓
ClickHouse
```

This means the MCP server lifecycle is owned by the ADK process.

A manually running MCP server in another terminal is not required for this configuration.

---

# Read-Only MCP Boundary

The production-style MCP configuration keeps:

```text
CLICKHOUSE_ALLOW_WRITE_ACCESS=false
```

The MCP interface is therefore currently restricted to database inspection and query operations.

Available tools:

```text
list_databases
list_tables
run_query
```

Consequential application writes continue through the existing controlled Python tools and still require human approval.

The architecture is currently:

```text
READ PATH

Director Agent
    ↓
Official ClickHouse MCP
    ↓
ClickHouse


CONTROLLED WRITE PATH

Director Agent
    ↓
Human Approval
    ↓
Existing Python Tool
    ↓
database.py
    ↓
ClickHouse
```

MCP has not been granted write authority.

---

# Environment Inheritance Issue Discovered

During the first production-style stdio test, the MCP child process unexpectedly started using HTTP transport.

The cause was an older shell environment variable from previous testing:

```text
CLICKHOUSE_MCP_SERVER_TRANSPORT=http
```

The ADK child process inherited the parent shell environment.

Because `clickhouse_mcp.py` included:

```python
env={
    **os.environ,
    ...
}
```

the previous HTTP setting leaked into the new stdio configuration.

The MCP process therefore started at:

```text
http://127.0.0.1:8000/mcp
```

while ADK was waiting for stdio communication.

The ADK MCP session eventually timed out.

---

# Explicit Transport Override

The reusable MCP configuration was corrected by explicitly setting:

```text
CLICKHOUSE_MCP_SERVER_TRANSPORT=stdio
```

inside the child-process environment.

This overrides any stale value inherited from the parent shell.

This produced the intended architecture:

```text
ADK
  ↓
McpToolset
  ↓
stdio
  ↓
mcp-clickhouse
```

An important development lesson was therefore:

```text
Inherited environment
        ≠
Intended child-process environment
```

Critical runtime configuration should be explicitly defined when subprocess behaviour depends on it.

---

# Production MCP Tool Discovery

The reusable `clickhouse_mcp` toolset was tested independently before attaching it to the Director Agent.

The official MCP server processed:

```text
ListToolsRequest
```

and ADK discovered:

```text
Tool count: 3

list_databases
list_tables
run_query
```

This verified:

```text
clickhouse_mcp.py
      ↓
ADK
      ↓
official mcp-clickhouse
      ↓
Tool discovery successful
```

---

# Director Agent Integration

The reusable MCP toolset was then added to the real Premiere root agent.

The existing specialist agents remained:

```text
Content Planning Agent
Content Generation Agent
Review Agent
```

The root agent now had six top-level tools/toolsets in total, including the read-only ClickHouse MCP integration.

An import check confirmed:

```text
Root Agent:
social_media_producer

Sub-agents:
content_planner
content_generator
review_agent

Tool count:
6
```

The existing direct ClickHouse tools were intentionally not removed.

This allows the project to migrate toward MCP incrementally rather than destabilising proven write workflows.

---

# Director MCP Read Rules

The Director Agent was instructed that:

* ClickHouse MCP access is read-only;
* stored campaign/content information may be retrieved through MCP;
* MCP should not be used for state changes;
* important writes must continue through controlled tools;
* explicit human approval remains required;
* MCP tool names must not be invented;
* database claims must be based on actual tool results.

This preserves the existing human-in-the-loop architecture while adding a new standardised read interface.

---

# Real Director Agent MCP Test

The normal Premiere application was launched through ADK Web.

The user asked:

```text
What is Campaign ID 3?

Use the ClickHouse MCP tools to query the social_producer database.

Do not answer from memory or from the existing list_campaigns tool.

Use MCP for this request.
```

The Director Agent returned the correct Campaign 3 data:

```text
Brand:
Ubuntu Frame Studios

Objective:
Build awareness and audience engagement leading up to the premiere.

Target Audience:
African film audiences aged 18 to 35

Platforms:
Instagram
TikTok
Facebook
YouTube

Duration:
28 days

Status:
draft

Created At:
2026-08-22 09:59:47
```

The returned values matched the independently verified ClickHouse state.

---

# ADK Trace Evidence

The correct response alone was not treated as sufficient proof of MCP usage.

The ADK execution trace was inspected.

The trace showed an actual tool invocation:

```json
{
  "name": "run_query",
  "response": {
    "isError": false
  }
}
```

The MCP tool returned:

```text
campaign_id = 3
brand_name = Ubuntu Frame Studios
objective = Build awareness and audience engagement leading up to the premiere.
target_audience = African film audiences aged 18 to 35
platforms = Instagram, TikTok, Facebook, YouTube
duration_days = 28
status = draft
created_at = 2026-08-22 09:59:47
```

The trace therefore independently proves:

```text
Director Agent
      ↓
run_query
      ↓
Official ClickHouse MCP
      ↓
ClickHouse
      ↓
Campaign 3
```

This is stronger evidence than inferring MCP use from the final natural-language answer.

---

# First Proven Production Director MCP Path

The following path has now been demonstrated end-to-end:

```text
User
  ↓
Premiere Director / Root Agent
  ↓
Google ADK
  ↓
McpToolset
  ↓
run_query
  ↓
Official mcp-clickhouse
  ↓
ClickHouse
  ↓
social_producer.campaigns
  ↓
Campaign 3
  ↓
Director response
```

The MCP request completed successfully and returned real application state.

---

# Current ClickHouse Architecture

Premiere currently uses two deliberately separated ClickHouse paths.

## Read / Agent Inspection Path

```text
Gemini / ADK
    ↓
Official ClickHouse MCP
    ↓
ClickHouse
```

## Human-Controlled Write Path

```text
Director Agent
    ↓
Explicit Human Approval
    ↓
Python Tool
    ↓
database.py
    ↓
clickhouse-connect
    ↓
ClickHouse
```

This architecture allows MCP integration to deepen without weakening the existing state-change safety boundaries.

---

# Director MCP Milestone Status

The following is now proven:

```text
[✓] Reusable ClickHouse MCP module created
[✓] MCP credentials loaded from local environment
[✓] MCP remains read-only
[✓] Stdio MCP child process configured
[✓] Environment-variable transport leak discovered
[✓] Transport explicitly pinned to stdio
[✓] ADK successfully discovered MCP tools
[✓] list_databases available
[✓] list_tables available
[✓] run_query available
[✓] Real Premiere Director Agent imports successfully with MCP
[✓] Existing specialist agents preserved
[✓] Director Agent given MCP read rules
[✓] Campaign 3 queried through real Director Agent
[✓] Actual run_query invocation observed in ADK trace
[✓] MCP returned real ClickHouse data
[✓] MCP tool result completed without error
[✓] Existing human-approved write path preserved
```

---

# Temporary MCP Test Harness

The temporary:

```text
mcp_test_app/
```

and:

```text
social_producer/mcp_test_agent.py
```

were created to isolate MCP testing before modifying the production Director Agent.

Now that the real Director Agent has successfully demonstrated MCP usage, those temporary testing components are no longer part of the intended production architecture.

They may be removed once their debugging value is no longer needed.

---

# Next ClickHouse Milestone — Agent Observability

With MCP now part of the real runtime, the next ClickHouse milestone is to start capturing agent execution events.

The planned table is:

```text
agent_events
```

Its purpose will be to record runtime behaviour such as:

```text
agent execution
delegation
tool calls
MCP calls
latency
success / failure
error codes
grounding decisions
model usage
```

This will move ClickHouse beyond campaign/content persistence into actual multi-agent observability.

The target architecture is:

```text
Director + Specialist Agents
        ↓
Execution Events
        ↓
agent_events
        ↓
ClickHouse
        ↓
Agent Reliability / Performance Analytics
```

This functionality has not yet been implemented.

## ClickHouse MCP Integration and Agent Observability

The AI Social Producer integrates **Google ADK agents with ClickHouse through the Model Context Protocol (MCP)**.

This allows the agent system to retrieve campaign and content information directly from ClickHouse while also recording agent execution telemetry back into ClickHouse.

### Architecture

The current data-grounding flow is:

```text
User
  ↓
Google ADK / Gemini
  ↓
social_media_producer
  ↓
MCP Toolset
  ↓
mcp-clickhouse
  ↓
ClickHouse
  ↓
Grounded Response
```

Agent activity is observed separately:

```text
Agent / Tool Execution
  ↓
ADK Callbacks
  ↓
Event Logger
  ↓
ClickHouse agent_events
```

ClickHouse therefore currently serves two important roles in the project:

1. **Application data storage**
   - `campaigns`
   - `content_items`

2. **Agent observability**
   - `agent_events`

---

### MCP Tools

The ClickHouse MCP integration currently exposes three read-only tools to the agent:

| Tool | Purpose |
|---|---|
| `list_databases` | Discover available ClickHouse databases |
| `list_tables` | Inspect tables and their schemas |
| `run_query` | Execute read-only SQL queries against ClickHouse |

The MCP server is launched automatically by Google ADK using **stdio transport**.

The agent therefore does **not** require a separately running MCP HTTP server.

Application writes continue to use the project's controlled Python database functions, while MCP access remains read-only.

```text
CLICKHOUSE_ALLOW_WRITE_ACCESS=false
```

---

### MCP Configuration

The ADK-to-ClickHouse MCP configuration is defined in:

```text
social_producer/clickhouse_mcp.py
```

The project uses Google ADK's `McpToolset` with `StdioConnectionParams`.

The MCP executable is installed permanently at:

```text
/home/gery/.local/bin/mcp-clickhouse
```

The MCP subprocess receives its ClickHouse connection settings from the project environment.

During development, an MCP lifecycle issue was encountered with the experimental graceful-error-handling path in the current Google ADK environment.

The development configuration therefore uses:

```text
ADK_DISABLE_MCP_GRACEFUL_ERROR_HANDLING=1
```

With this configuration, ADK successfully initialises the MCP session and discovers the ClickHouse tools.

---

### Verified MCP Grounding

The integration was tested end-to-end using **Campaign ID 3**.

The `social_media_producer` agent was explicitly instructed to retrieve the campaign directly from ClickHouse through MCP instead of using the application's `list_campaigns` tool.

The MCP `run_query` tool successfully returned:

| Field | Value |
|---|---|
| Campaign ID | 3 |
| Brand Name | Ubuntu Frame Studios |
| Objective | Build awareness and audience engagement leading up to the premiere |
| Target Audience | African film audiences aged 18 to 35 |
| Platforms | Instagram, TikTok, Facebook, YouTube |
| Duration | 28 days |
| Status | draft |

This verifies the following runtime path:

```text
User Request
      │
      ▼
social_media_producer
      │
      ▼
MCP run_query
      │
      ▼
ClickHouse
      │
      ▼
Campaign Data
      │
      ▼
Gemini Grounded Response
```

The response returned by the agent matched the data stored in ClickHouse.

---

## Agent Observability

The project also records agent and tool execution telemetry in ClickHouse.

The `agent_events` table provides visibility into how the multi-agent system behaves at runtime.

### agent_events Schema

The table currently records:

| Column | Purpose |
|---|---|
| `event_id` | Unique event identifier |
| `session_id` | ADK session associated with the event |
| `parent_agent` | Parent agent where applicable |
| `agent_name` | Agent responsible for the event |
| `event_type` | Type of agent event |
| `tool_name` | Tool that was executed |
| `campaign_id` | Related campaign when available |
| `content_id` | Related content item when available |
| `status` | Execution status |
| `error_code` | Error information when execution fails |
| `model_name` | Gemini model associated with the execution |
| `grounding_result` | Grounding/review result when applicable |
| `latency_ms` | Tool execution latency |
| `input_tokens` | Input token telemetry |
| `output_tokens` | Output token telemetry |
| `created_at` | Event timestamp |

This provides the foundation for analysing:

- agent activity;
- tool usage;
- tool failures;
- execution latency;
- grounding behaviour;
- campaign-related agent activity;
- content-related agent activity; and
- model usage.

---

### Verified Automatic MCP Telemetry

A live ADK session successfully produced the following automatic MCP events:

| Event ID | Tool | Status | Latency |
|---:|---|---|---:|
| 11 | `list_databases` | success | 1,751 ms |
| 12 | `list_tables` | success | 2,545 ms |
| 13 | `run_query` | success | 919 ms |

All three events were generated under the same ADK session:

```text
e-0189a426-cb92-4ce3-8376-64d28c32d7ac
```

This proves that MCP execution is not only working but is also being captured automatically by the project's observability layer.

The complete flow is now:

```text
                         ┌──────────────────────┐
                         │        User          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Google ADK / Gemini  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │  social_media_producer    │
                      └─────────────┬─────────────┘
                                    │
                       ┌────────────┴────────────┐
                       │                         │
                       ▼                         ▼
              ┌─────────────────┐       ┌─────────────────┐
              │  MCP Toolset    │       │  ADK Callbacks  │
              └────────┬────────┘       └────────┬────────┘
                       │                         │
                       ▼                         ▼
              ┌─────────────────┐       ┌─────────────────┐
              │ mcp-clickhouse  │       │  Event Logger   │
              └────────┬────────┘       └────────┬────────┘
                       │                         │
                       └────────────┬────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     ClickHouse       │
                         ├──────────────────────┤
                         │ campaigns            │
                         │ content_items        │
                         │ agent_events         │
                         └──────────────────────┘
```

---

### Current Observability Limitation

Generic MCP `run_query` events currently record:

```text
campaign_id = NULL
content_id  = NULL
```

even when the SQL query targets a specific campaign.

This happens because the MCP callback receives a SQL statement such as:

```sql
SELECT ...
FROM social_producer.campaigns
WHERE campaign_id = 3
```

rather than receiving `campaign_id` as a separate structured tool argument.

The query itself is still successfully executed and the MCP event is correctly recorded.

A later observability enhancement can extract entity identifiers from MCP query metadata or introduce additional query metadata fields.

---

## MCP Troubleshooting Notes

During integration, direct MCP testing worked before MCP tool discovery worked reliably inside the full ADK application.

The debugging process confirmed each layer independently:

```text
ClickHouse connectivity          ✓
mcp-clickhouse installation      ✓
stdio transport                  ✓
MCP ClientSession                ✓
MCP initialise handshake         ✓
MCP list_tools                   ✓
Google ADK McpToolset            ✓
MCP run_query                    ✓
Grounded agent response          ✓
Automatic agent telemetry        ✓
```

An important lesson from this debugging process is that **an MCP server being reachable does not automatically mean its tools have been successfully registered with an agent**.

The final integration verifies the complete path from the ADK agent, through MCP, into ClickHouse and back to the model.

---

## Current ClickHouse Integration Status

| Capability | Status |
|---|---|
| Campaign storage | ✅ Working |
| Content item storage | ✅ Working |
| ClickHouse Python client | ✅ Working |
| MCP server | ✅ Working |
| MCP stdio transport | ✅ Working |
| ADK MCP tool discovery | ✅ Working |
| `list_databases` | ✅ Working |
| `list_tables` | ✅ Working |
| `run_query` | ✅ Working |
| Campaign grounding through MCP | ✅ Working |
| Agent event logging | ✅ Working |
| Automatic MCP telemetry | ✅ Working |
| Tool latency tracking | ✅ Working |
| Campaign ID extraction from MCP SQL | ⏳ Planned |
| Token telemetry | ⏳ Planned |
| ClickHouse agent analytics | ⏳ Next phase |

### Next Phase

The next phase will build analytics on top of `agent_events` so that ClickHouse can be used to analyse the behaviour of the agent system itself.

Planned analytics include:

- tool usage frequency;
- tool success and failure rates;
- average and percentile latency;
- agent activity by session;
- campaign-related agent activity;
- grounding success;
- error patterns;
- model usage; and
- token usage when available.

This will extend ClickHouse from being only the application's operational data store into an **analytics and observability platform for the multi-agent system**.

## Closed-Loop Campaign Optimisation

The AI Social Producer now supports an evidence-driven campaign optimisation loop in which campaign performance data stored in ClickHouse can influence future content planning.

This is an important architectural milestone because the system no longer only generates campaign content. It can observe campaign results, analyse performance, propose improvements, require human approval, and feed approved recommendations back into the planning process.

### Architecture

```text
Campaign Content
       │
       ▼
Engagement Events
       │
       ▼
ClickHouse
engagement_events
       │
       ▼
Materialized View
       │
       ▼
content_performance_daily
       │
       ├──────────────────────────┐
       ▼                          ▼
Analytics Agent            Optimisation Agent
       │                          │
       │                    Observations
       │                    Hypotheses
       │                    Recommendations
       │                    Experiments
       │                    Success Metrics
       │                          │
       │                          ▼
       │              optimisation_recommendations
       │                          │
       │                          ▼
       │                    Human Approval
       │                          │
       └──────────────────────────┤
                                  ▼
                           Content Planner
                                  │
                                  ▼
                       Adaptive Content Proposal
                                  │
                                  ▼
                            Human Review
```

---

### Engagement Event Storage

Raw campaign engagement events are stored in:

```text
social_producer.engagement_events
```

The table records engagement signals including:

- impressions
- views
- likes
- comments
- shares
- saves
- clicks

Events are associated with:

- campaign ID
- content ID
- platform
- event type
- event value
- source
- occurrence time

This provides the raw event stream used for campaign-performance analysis.

---

### Real-Time Performance Aggregation

Campaign engagement events are automatically aggregated through a ClickHouse Materialized View:

```text
mv_content_performance_daily
```

The resulting roll-up table is:

```text
content_performance_daily
```

It uses `SummingMergeTree` to maintain aggregated daily performance metrics for each:

```text
date
campaign
content item
platform
```

This means the agents do not need to repeatedly scan and aggregate the complete raw engagement-event dataset when evaluating campaign performance.

---

## Campaign 3 Test Dataset

The optimisation workflow was tested using:

**Campaign ID:** 3  
**Film:** Shadows of Pretoria  
**Brand:** Ubuntu Frame Studios  
**Objective:** Build awareness and audience engagement leading up to the premiere.  
**Target Audience:** African film audiences aged 18–35  
**Platforms:** Instagram, TikTok, Facebook and YouTube

The current engagement dataset is simulated for development and demonstration purposes.

It must therefore not be represented as real production social-media performance data.

---

## Campaign Analytics

Campaign-level and platform-level analytics functions were implemented to retrieve aggregated performance data from ClickHouse.

The system successfully identified different performance characteristics across platforms.

### Platform Performance

| Platform | Impressions | Views | Clicks | Engagement Rate | Click Rate |
|---|---:|---:|---:|---:|---:|
| TikTok | 82,400 | 69,200 | 1,320 | 19.08% | 1.60% |
| Instagram | 42,520 | 24,130 | 1,236 | 11.35% | 2.91% |
| YouTube | 39,100 | 25,600 | 870 | 8.42% | 2.23% |
| Facebook | 9,100 | 3,900 | 142 | 6.18% | 1.56% |

The test demonstrated that the system can distinguish between different optimisation objectives.

For example:

- TikTok produced the strongest reach and engagement.
- Instagram produced the highest click-through rate.
- YouTube showed stronger performance for promotional content than general awareness content.
- Facebook was the weakest-performing platform in the simulated dataset.

The system therefore does not treat the single largest metric as automatically representing the "best" platform.

---

## Analytics Agent

The Analytics Agent is responsible for interpreting campaign-performance data.

It can analyse:

- campaign performance
- platform performance
- strongest content
- underperforming content
- engagement behaviour
- click behaviour

The Analytics Agent is separate from the operational observability system.

### Campaign Analytics

Answers questions such as:

```text
Which platform performed best?

Which content generated the most engagement?

Which content generated the most clicks?

Which content underperformed?
```

### Agent Observability

The separate observability system analyses the AI application itself:

```text
tool latency
tool failures
agent sessions
MCP calls
model execution
agent reliability
```

This distinction is intentional:

```text
Campaign Analytics
        =
How well is the marketing campaign performing?

Agent Observability
        =
How well is the AI system performing?
```

Both datasets are stored and analysed using ClickHouse.

---

## Optimisation Agent

A dedicated `optimisation_agent` was added to the multi-agent architecture.

The agent currently has read-only access to:

```text
get_campaign_performance
get_platform_performance
```

Its responsibility is to convert campaign-performance evidence into structured optimisation advice.

It separates its reasoning into:

1. Observations
2. Hypotheses
3. Recommendations
4. Proposed experiments
5. Success metrics

The Optimisation Agent does not directly modify campaigns.

This is an intentional safety boundary.

---

## Persisted Optimisation Recommendations

Optimisation recommendations are stored in:

```text
social_producer.optimisation_recommendations
```

Each recommendation contains:

```text
recommendation_id
campaign_id
recommendation_type
observation
hypothesis
recommendation
experiment
success_metric
status
created_at
```

This allows optimisation decisions to become persistent campaign knowledge rather than disappearing after an LLM conversation.

---

## First Persisted Recommendation

Campaign 3 produced the first stored optimisation recommendation.

**Recommendation ID:** 1

### Observation

TikTok generated:

```text
82,400 impressions
69,200 views
19.08% engagement rate
1.60% click rate
```

TikTok therefore demonstrated strong awareness and engagement performance but weaker click-through efficiency.

### Hypothesis

Adding a stronger action-oriented CTA to a high-engagement TikTok format may improve click-through performance.

### Recommendation

Test a CTA-oriented TikTok post while preserving the behind-the-scenes or atmosphere format that performed strongly.

### Experiment

Create a TikTok experiment combining a high-engagement creative format with an explicit verified campaign CTA.

### Success Metric

```text
TikTok click rate > 1.60%
```

while avoiding a substantial reduction in engagement.

---

## Human Approval Boundary

Optimisation recommendations are not automatically executed.

The Optimisation Agent remains read-only.

Approval is controlled by the root Social Media Producer/Director.

The workflow is:

```text
Optimisation Agent
       │
       ▼
PROPOSED recommendation
       │
       ▼
Human review
       │
       ▼
Director approval
       │
       ▼
APPROVED recommendation
```

This prevents an analytical agent from changing campaign strategy autonomously.

---

## ClickHouse Mutation Design

An important ClickHouse-specific issue was encountered while implementing recommendation approval.

The original table ordering included:

```text
status
```

An attempt to update the recommendation status therefore produced:

```text
DB::Exception:
Cannot UPDATE key column `status`.
(CANNOT_UPDATE_COLUMN)
```

This occurred because ClickHouse does not permit mutation of a column that participates in the sorting key.

The table design was corrected so that mutable workflow state is not part of the immutable ordering key.

This was an important architectural lesson when modelling workflow state in ClickHouse.

---

## Planner Integration

The Content Planner was extended with:

```text
get_optimisation_recommendations
```

Its tools now include:

```text
get_campaign_by_id
list_campaign_content
get_optimisation_recommendations
```

The Planner can therefore inspect:

1. the campaign definition;
2. existing campaign content;
3. optimisation recommendations.

However, it is instructed to use only recommendations whose status is:

```text
approved
```

Proposed or rejected recommendations must not influence adaptive planning.

---

## First Closed-Loop Planning Test

The first complete optimisation-feedback test was successfully performed against Campaign 3.

The Planner retrieved approved Recommendation ID 1 and proposed:

**Platform:** TikTok  
**Content Type:** Engagement / Call-to-Action experiment  
**Topic:** TikTok Atmosphere & Premiere Reminder Experiment  
**Suggested Campaign Day:** Day 19

### Experiment Purpose

Test whether combining TikTok's high-engagement atmosphere format with an explicit verified premiere-date CTA can increase click-through performance.

### Success Metric

```text
TikTok CTR > 1.60%
```

without substantially reducing engagement.

The Planner correctly stated that the proposal was:

```text
Human review only
```

and did not:

```text
save content
schedule content
publish content
modify existing campaign content
```

---

## Closed-Loop Optimisation Milestone

The following loop has now been demonstrated:

```text
        ┌─────────────────────────┐
        │     Campaign Content    │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │    Engagement Events    │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │       ClickHouse        │
        │ Analytics + Aggregation │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │     Analytics Agent     │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │   Optimisation Agent    │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │     Recommendation      │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │      Human Approval     │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │     Content Planner     │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │  Experimental Proposal  │
        └────────────┬────────────┘
                     │
                     ▼
               Human Review
```

This demonstrates that ClickHouse is not being used only as passive storage.

It acts as the analytical memory and feedback layer connecting campaign execution, performance analysis, optimisation recommendations and future agent decisions.

---

## ClickHouse Track Alignment

The project currently demonstrates several important ClickHouse capabilities.

### Implemented

- MergeTree event storage
- high-volume-style engagement event modelling
- Materialized Views
- SummingMergeTree performance aggregation
- campaign analytics
- agent execution observability
- tool latency and reliability analytics
- persistent optimisation recommendations
- ClickHouse MCP integration
- LLM access to ClickHouse through MCP
- multi-agent decision flow
- human-controlled optimisation approval
- data-driven adaptive content planning

### Still Planned

The next ClickHouse-focused capabilities include:

- materialized operational agent-performance rollups
- richer recommendation lifecycle tracking
- experiment-result comparison
- automatic baseline-vs-experiment analysis
- recommendation outcome tracking
- vector embeddings for campaign assets
- ClickHouse native vector similarity search
- hybrid metadata + semantic asset retrieval

---

## Current Multi-Agent Architecture

```text
                    Social Media Producer
                         (Director)
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
 Content Planner      Content Generator       Review Agent
          │
          │
          ├───────────────────────────────┐
          │                               │
          ▼                               ▼
 Analytics Agent                 Optimisation Agent
                                          │
                                          ▼
                              Optimisation Recommendation
                                          │
                                          ▼
                                  Human Approval
                                          │
                                          └──────► Planner feedback
```

The root Director remains responsible for coordinating agents and controlling write operations.

---

## Current Project Position

The project has moved beyond:

```text
Prompt → LLM → social media post
```

and now demonstrates:

```text
Plan
 ↓
Generate
 ↓
Review
 ↓
Measure
 ↓
Analyse
 ↓
Optimise
 ↓
Human Approve
 ↓
Re-plan
 ↓
Experiment
 ↓
Measure Again
```

The next major milestone is to persist the approved experimental content item, generate controlled simulated results for the experiment, and allow the analytics/optimisation layer to determine whether Recommendation ID 1 actually improved campaign performance.


# Development Update: Verified Campaign Fact Grounding

**Date:** 24 August 2026  
**Project:** Premiere — AI Studio Producer  
**Campaign:** Campaign ID 3 — Shadows of Pretoria

---

## 1. Problem Identified

During generation of **Content ID 14**, the Content Generation Agent needed to include the premiere date for *Shadows of Pretoria*.

The first generated draft contained:

> The atmosphere is building. 🎬✨
>
> Get ready for the official premiere on [Insert Verified Premiere Date].
>
> Are you ready? Let us know in the comments below! 👇

The Content Generator correctly refused to invent the premiere date.

The problem was not that the premiere date was unknown to us. We had already established that the premiere date was **20 October 2026**.

The problem was architectural:

**The premiere date was not stored in a structured source of verified facts that the Content Generator could retrieve.**

This demonstrated an important grounding principle for the project:

> Information discussed during development should not automatically be treated as verified information by an AI agent.

The agent needs an explicit, retrievable source of trusted facts.

---

## 2. Solution: Verified Campaign Facts

A new ClickHouse table was created:

`campaign_facts`

Its purpose is to store factual campaign information that has been explicitly verified and can therefore be safely used by agents.

The table was created with:

```sql
CREATE TABLE IF NOT EXISTS social_producer.campaign_facts
(
    campaign_id UInt64,
    fact_key String,
    fact_value String,
    verification_status LowCardinality(String) DEFAULT 'verified',
    source String DEFAULT 'human',
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (campaign_id, fact_key);
```

This introduces a distinction between:

- campaign planning information;
- verified factual information;
- generated content;
- performance data.

---

## 3. Verified Facts Added for Campaign 3

Four verified facts were added for Campaign ID 3.

| Fact Key | Value | Verification Status | Source |
|---|---|---|---|
| `project_title` | Shadows of Pretoria | verified | human |
| `project_type` | Fictional crime drama | verified | human |
| `premiere_date` | 2026-10-20 | verified | human |
| `primary_market` | South Africa | verified | human |

These facts were inserted using:

```sql
INSERT INTO social_producer.campaign_facts
    (campaign_id, fact_key, fact_value, verification_status, source)
VALUES
    (3, 'project_title', 'Shadows of Pretoria', 'verified', 'human'),
    (3, 'project_type', 'Fictional crime drama', 'verified', 'human'),
    (3, 'premiere_date', '2026-10-20', 'verified', 'human'),
    (3, 'primary_market', 'South Africa', 'verified', 'human');
```

---

## 4. Verification in ClickHouse

The records were checked directly from the running ClickHouse Docker container.

Command:

```bash
docker exec -it clickhouse-server clickhouse-client \
  --user social_producer \
  --database social_producer \
  --query "
SELECT
    campaign_id,
    fact_key,
    fact_value,
    verification_status,
    source
FROM campaign_facts
WHERE campaign_id = 3
ORDER BY fact_key;
"
```

The result confirmed:

```text
3   premiere_date    2026-10-20             verified   human
3   primary_market   South Africa           verified   human
3   project_title    Shadows of Pretoria    verified   human
3   project_type     Fictional crime drama  verified   human
```

The verified facts were therefore successfully stored in ClickHouse.

---

## 5. Python Database Integration

A new function was added to:

`social_producer/database.py`

The function is:

```python
get_campaign_facts(campaign_id)
```

Its responsibility is to retrieve campaign facts from the `campaign_facts` ClickHouse table.

An initial implementation attempted to use:

```python
client = get_client()
```

However, `database.py` did not contain a `get_client()` function.

This resulted in:

```text
NameError: name 'get_client' is not defined
```

The project already had a module-level ClickHouse client created near the top of `database.py`.

The function was therefore corrected to use the existing `client`.

After the fix, the function was tested with:

```bash
python -c "from social_producer.database import get_campaign_facts; print(get_campaign_facts(3))"
```

The result was:

```python
[
    {
        'fact_key': 'premiere_date',
        'fact_value': '2026-10-20',
        'verification_status': 'verified',
        'source': 'human'
    },
    {
        'fact_key': 'primary_market',
        'fact_value': 'South Africa',
        'verification_status': 'verified',
        'source': 'human'
    },
    {
        'fact_key': 'project_title',
        'fact_value': 'Shadows of Pretoria',
        'verification_status': 'verified',
        'source': 'human'
    },
    {
        'fact_key': 'project_type',
        'fact_value': 'Fictional crime drama',
        'verification_status': 'verified',
        'source': 'human'
    }
]
```

This confirmed that Python could successfully retrieve the verified facts from ClickHouse.

---

## 6. Content Generator Upgrade

Before this change, the Content Generator used two main sources of information:

```text
Content Item
     +
Campaign
     ↓
Content Generator
```

This was insufficient for factual grounding.

The Content Generator architecture was upgraded to:

```text
Content Item
     ↓
Campaign
     ↓
Verified Campaign Facts
     ↓
Content Generator
     ↓
Grounded Draft
```

The Content Generator now has access to:

1. the planned content item;
2. the campaign context;
3. verified campaign facts.

---

## 7. New Content Generator Tool

A new tool was added:

```python
get_verified_campaign_facts(campaign_id)
```

This tool retrieves campaign facts and exposes only facts whose verification status is:

```text
verified
```

Conceptually:

```text
campaign_facts
      ↓
get_campaign_facts()
      ↓
Filter verification_status == "verified"
      ↓
get_verified_campaign_facts()
      ↓
Content Generator
```

This means the Content Generator now has a structured source of facts that it is explicitly allowed to use.

---

## 8. Grounding Rules Added to the Content Generator

The Content Generator was instructed to distinguish between **planning information** and **verified factual information**.

### Planning Information

Examples include:

- content topic;
- content purpose;
- content type;
- campaign objective.

Planning information describes what the content should discuss.

It does **not** prove that a factual claim is true.

For example:

```text
Topic:
Behind-the-Scenes Production Teaser
```

does not automatically prove that behind-the-scenes footage exists.

### Verified Information

Verified information comes from the campaign facts system.

For Campaign ID 3, examples include:

```text
project_title  = Shadows of Pretoria
project_type   = Fictional crime drama
premiere_date  = 2026-10-20
primary_market = South Africa
```

These facts can be used in generated content because they have been explicitly verified.

---

## 9. Anti-Hallucination Rules

The Content Generator was explicitly instructed not to invent:

- statistics;
- testimonials;
- cast members;
- characters;
- plot details;
- filming locations;
- film setting;
- reviews;
- awards;
- quotes;
- premiere venue;
- ticket availability;
- ticket links;
- streaming availability;
- streaming links;
- distribution information;
- promotional assets that have not been verified.

An important rule was also added:

> Do not infer facts from a film title.

For example:

```text
Shadows of Pretoria
```

does **not** prove:

```text
The film is set in Pretoria.
```

The title and the setting are separate facts.

Unless the setting is stored as a verified campaign fact, the Content Generator must not make that claim.

---

## 10. Content ID 14 Grounding Test

The new grounding architecture was tested using **Content ID 14**.

### Content Item Details

**Content ID:** 14  
**Campaign ID:** 3  
**Platform:** TikTok  
**Content Type:** experiment  
**Campaign Day:** 19  
**Status:** planned

**Topic:**

> TikTok Atmosphere & Premiere Reminder Experiment

**Purpose:**

> Test whether combining TikTok's high-engagement atmosphere format with an explicit verified premiere-date call-to-action can increase click-through performance above the current TikTok baseline.

---

## 11. Result Before Verified Facts

Before the `campaign_facts` integration, the Content Generator produced:

> The atmosphere is building. 🎬✨
>
> Get ready for the official premiere on [Insert Verified Premiere Date].
>
> Are you ready? Let us know in the comments below! 👇

It also reported that no verified premiere date was available.

This was actually correct behaviour.

The agent did **not hallucinate a date**.

Instead, it stopped and requested verified information.

The failure was therefore not an AI safety failure.

It revealed a missing piece in our data architecture.

---

## 12. Result After Verified Facts

After adding `campaign_facts` and giving the Content Generator access to `get_verified_campaign_facts()`, Content ID 14 was tested again.

The Content Generator successfully retrieved:

- **Project Title:** Shadows of Pretoria
- **Project Type:** Fictional crime drama
- **Premiere Date:** 2026-10-20
- **Primary Market:** South Africa

It then generated:

> Shadows of Pretoria arrives on October 20, 2026. Mark your calendars for the premiere of this fictional crime drama! 🎬✨ #ShadowsOfPretoria #SouthAfrica #FilmPremiere

The agent also correctly reported:

> Nothing has been saved. Stopped for human review.

This confirms that the grounding pipeline worked while preserving the human approval boundary.

---

## 13. Human Review

The generated copy was grounded, but a small wording improvement was identified.

The phrase:

> Shadows of Pretoria arrives on October 20, 2026.

was changed to:

> Shadows of Pretoria premieres on 20 October 2026.

This maps more directly to the stored fact:

```text
premiere_date = 2026-10-20
```

### Human-Reviewed Draft

> Shadows of Pretoria premieres on 20 October 2026. Mark your calendars for this fictional crime drama. 🎬✨  
> #ShadowsOfPretoria #SouthAfrica #FilmPremiere

This is the currently approved wording for the next stage of the workflow.

---

## 14. Why This Change Matters

This is an important architectural improvement.

Previously, the system effectively had:

```text
Campaign
    ↓
Content Plan
    ↓
AI Generation
```

The improved system now has:

```text
Campaign
    ↓
Content Plan
    ↓
Verified Facts
    ↓
AI Generation
```

The AI is no longer expected to decide by itself which campaign information should be trusted as factual.

Instead, factual claims can be grounded against structured ClickHouse records.

---

## 15. Current Data Responsibilities

The project is developing a clear separation of responsibilities.

### `campaigns`

Stores high-level campaign configuration.

Examples:

- objective;
- target audience;
- platforms;
- duration;
- campaign status.

### `content_items`

Stores the content plan and generated content lifecycle.

Examples:

- platform;
- content type;
- topic;
- content purpose;
- campaign day;
- generated copy;
- status.

### `campaign_facts`

Stores verified factual information that agents may use as evidence.

Examples:

- project title;
- premiere date;
- project type;
- primary market.

### `content_performance_daily`

Stores aggregated campaign/content performance.

Examples:

- impressions;
- views;
- likes;
- comments;
- shares;
- saves;
- clicks.

### `optimisation_recommendations`

Stores optimisation decisions and recommendations generated from performance analysis.

---

## 16. Current Agentic Flow

The project can now demonstrate the following workflow:

```text
Campaign
   ↓
Content Planning
   ↓
Content Published / Simulated
   ↓
ClickHouse Performance Data
   ↓
Analytics Agent
   ↓
Performance Analysis
   ↓
Optimisation Agent
   ↓
Optimisation Recommendation
   ↓
Human Approval
   ↓
Content Planner
   ↓
New Experiment Content Item
   ↓
Content Generator
   ↓
Verified Campaign Facts from ClickHouse
   ↓
Grounded Draft
   ↓
Human Review
   ↓
Review Agent
   ↓
Approved Content
```

For the current experiment:

```text
Campaign ID 3
     ↓
Performance Data
     ↓
Analytics Agent
     ↓
TikTok:
High engagement / lower CTR

Instagram:
Lower engagement / higher CTR
     ↓
Optimisation Agent
     ↓
Hypothesis:
Test stronger CTA behaviour
     ↓
Human Approval
     ↓
Content Planner
     ↓
Content ID 14
TikTok Atmosphere &
Premiere Reminder Experiment
     ↓
Content Generator
     ↓
campaign_facts
     ↓
Verified premiere date:
20 October 2026
     ↓
Grounded TikTok Draft
     ↓
Human Review
     ← CURRENT POSITION
```

---

## 17. ClickHouse's Expanded Role

ClickHouse is now serving more than one purpose in the project.

It is being used for:

### Campaign State

Campaign and content records are stored and retrieved from ClickHouse.

### Performance Analytics

Engagement and performance data is aggregated and analysed from ClickHouse.

### Optimisation

Performance data is used by the Optimisation Agent to produce recommendations and experiments.

### Grounding

Verified campaign facts stored in ClickHouse are now used by the Content Generator to prevent unsupported factual claims.

This creates a loop:

```text
CREATE
   ↓
PUBLISH / SIMULATE
   ↓
MEASURE
   ↓
ClickHouse
   ↓
ANALYSE
   ↓
OPTIMISE
   ↓
PLAN
   ↓
GROUND
   ↓
GENERATE
   ↓
REVIEW
   ↓
CREATE AGAIN
```

---

## 18. Milestone Achieved

The project has now demonstrated an end-to-end connection between:

- campaign planning;
- content generation;
- ClickHouse storage;
- performance analytics;
- optimisation;
- experiment creation;
- verified factual grounding;
- human approval.

Most importantly, the system demonstrated that an agent can recognise when it lacks verified information, refuse to invent that information, retrieve newly supplied verified facts from ClickHouse, and then regenerate grounded content using those facts.

---

## 19. Current Position

**Content ID 14 is currently at the human-review stage.**

The reviewed copy is:

> Shadows of Pretoria premieres on 20 October 2026. Mark your calendars for this fictional crime drama. 🎬✨  
> #ShadowsOfPretoria #SouthAfrica #FilmPremiere

The content has **not yet been saved as the final draft**.

---

## 20. Next Step

The next development steps are:

1. Save the human-reviewed copy for **Content ID 14**.
2. Confirm that its status changes appropriately from `planned` to `draft`.
3. Send Content ID 14 to the **Review Agent**.
4. Verify that the Review Agent passes the grounded content.
5. Continue the experiment lifecycle.
6. Later simulate or ingest performance for Content ID 14.
7. Compare its TikTok CTR against the existing TikTok baseline.
8. Determine whether the optimisation hypothesis was supported.

---

**Development checkpoint:** Verified campaign-fact grounding is working end-to-end.


# Development Update: Closed-Loop Optimisation Experiment Completed

**Date:** 25 August 2026  
**Project:** Premiere — AI Studio Producer  
**Campaign:** Campaign ID 3 — Shadows of Pretoria  
**Recommendation:** Recommendation ID 1  
**Experiment Content:** Content ID 14

---

## 1. Objective

The objective of this milestone was to complete the first full optimisation experiment generated from campaign-performance evidence.

The system had previously identified that TikTok generated strong engagement but comparatively weaker click-through performance.

The established TikTok baseline was:

```text
Impressions:       82,400
Views:             69,200
Engagement Rate:   19.08%
Click Rate:         1.60%
```

This led to the hypothesis that combining TikTok's high-engagement atmosphere format with a stronger click-oriented call-to-action could improve click-through performance without substantially reducing engagement.

---

## 2. Persisted Optimisation Recommendation

The first optimisation recommendation had already been persisted in:

```text
social_producer.optimisation_recommendations
```

The stored record was independently queried.

Schema:

```text
recommendation_id
campaign_id
recommendation_type
observation
hypothesis
recommendation
experiment
experiment_content_id
success_metric
status
created_at
```

Recommendation ID 1 currently contains:

```text
recommendation_id:
1

campaign_id:
3

recommendation_type:
platform_experiment

observation:
TikTok generated 82,400 impressions and 69,200 views with
a 19.08% engagement rate, but its click rate was 1.60%.

hypothesis:
Adding a stronger action-oriented CTA to a high-engagement
TikTok format may increase click-through performance.

recommendation:
Test a CTA-oriented TikTok post while preserving the
behind-the-scenes or atmosphere format that performed strongly.

experiment:
Create a TikTok experiment combining a high-engagement
creative format with an explicit verified campaign CTA.

experiment_content_id:
14

success_metric:
TikTok click rate exceeds the current 1.60% baseline without
a substantial reduction in engagement.

status:
applied_to_plan
```

This independently confirms the relationship:

```text
Recommendation ID 1
        ↓
Campaign ID 3
        ↓
Experiment Content ID 14
```

---

## 3. Experiment Content Item

The approved optimisation recommendation was fed back into the Content Planning Agent.

The resulting experiment was persisted as:

```text
Content ID:       14
Campaign ID:      3
Platform:         TikTok
Content Type:     experiment
Campaign Day:     19
Status:           planned
```

Topic:

```text
TikTok Atmosphere & Premiere Reminder Experiment
```

Purpose:

```text
Test whether combining TikTok's high-engagement atmosphere
format with an explicit verified premiere-date call-to-action
can increase click-through performance above the current
TikTok baseline.
```

The Content ID 14 record was independently re-queried from ClickHouse through the Python data layer.

---

## 4. Grounding Problem Discovered

The first attempt to generate Content ID 14 exposed a grounding limitation.

The Content Generation Agent returned:

> Get ready for the official premiere on [Insert Verified Premiere Date].

Although the premiere date had previously been established during development, it was not available through the agent's accessible campaign data.

The agent correctly refused to invent the missing date.

This demonstrated that:

```text
Information discussed with a human
        ≠
Structured verified information available to an agent
```

---

## 5. Verified Campaign Fact Layer

A new ClickHouse table was therefore introduced:

```text
campaign_facts
```

The table stores facts explicitly verified for a campaign.

Campaign 3 currently contains:

```text
project_title:
Shadows of Pretoria

project_type:
Fictional crime drama

premiere_date:
2026-10-20

primary_market:
South Africa
```

All four records use:

```text
verification_status = verified
source = human
```

The Content Generation Agent was upgraded with access to:

```text
get_verified_campaign_facts()
```

This allowed the generator to distinguish between planning information and factual evidence.

---

## 6. CTR Experiment Dependency Discovered

After grounding the premiere date, the Review Agent identified another problem.

The experiment was intended to improve:

```text
Click-Through Rate
```

but the generated copy used an engagement-oriented CTA:

```text
Drop a comment below...
```

The Review Agent correctly returned:

```text
REVISE
```

because a comment-based CTA does not directly test click-through behaviour.

However, the Review Agent suggested using a link in the bio to set a reminder.

That functionality had not been verified.

This revealed another important grounding principle:

```text
A correct review classification
        ≠
A automatically grounded suggested rewrite
```

The campaign therefore required a verified click destination before a CTR experiment could be meaningfully tested.

---

## 7. Simulated CTA Destination

Because Campaign 3 is a fictional development campaign, a clearly simulated campaign destination was added.

Verified campaign facts were extended with:

```text
cta_type:
simulated_premiere_landing_page

cta_url:
https://premiere.example/shadows-of-pretoria
```

The `.example` domain was intentionally used so the destination could not be confused with a real production website.

The complete Campaign 3 verified-fact set became:

```text
cta_type
    → simulated_premiere_landing_page

cta_url
    → https://premiere.example/shadows-of-pretoria

premiere_date
    → 2026-10-20

primary_market
    → South Africa

project_title
    → Shadows of Pretoria

project_type
    → Fictional crime drama
```

These values were independently retrieved from ClickHouse after insertion.

---

## 8. Final Grounded Experiment Draft

The Content Generation Agent retrieved:

- Content ID 14;
- Campaign ID 3 context;
- verified campaign facts;
- the simulated campaign CTA destination.

The final human-approved draft was:

> The atmosphere is shifting. Get ready for the premiere of the fictional crime drama Shadows of Pretoria on 20 October 2026.
>
> Visit the campaign page to learn more:  
> https://premiere.example/shadows-of-pretoria 🔗✨
>
> #ShadowsOfPretoria #FilmPremiere

The draft avoids unsupported claims involving:

- tickets;
- ticket sales;
- RSVP functionality;
- reminders;
- venue information;
- streaming availability;
- cast;
- plot;
- setting.

---

## 9. Draft Persistence

The final human-approved experiment copy was persisted using:

```python
save_generated_content(14, content_text)
```

The write returned:

```text
saved = True
content_id = 14
status = draft
```

An independent re-query confirmed:

```text
content_id:
14

campaign_id:
3

platform:
TikTok

content_type:
experiment

status:
draft
```

The stored `content_text` matched the human-approved experiment copy.

---

## 10. Review Agent Result

The persisted Content ID 14 draft was submitted to the Review Agent.

The agent evaluated:

- factual grounding;
- experiment-purpose alignment;
- TikTok suitability;
- atmosphere-oriented framing;
- verified premiere date;
- verified CTA destination;
- unsupported functionality or claims.

The Review Agent returned:

```text
Recommendation: PASS
```

It reported:

```text
Issues: None

Suggested changes: None
```

Content ID 14 therefore successfully passed the project's review stage.

---

## 11. Experiment Success Criteria

The original success metric stored with Recommendation ID 1 was:

```text
TikTok click rate exceeds the current 1.60% baseline
without a substantial reduction in engagement.
```

Before inserting the simulated experiment result, this was converted into explicit development thresholds.

Baseline:

```text
TikTok CTR:
1.60%

TikTok Engagement Rate:
19.08%
```

Experiment success criteria:

```text
CTR > 1.60%

AND

Engagement Rate >= 17.08%
```

The 17.08% floor represents a maximum tolerated engagement reduction of:

```text
2.00 percentage points
```

from the 19.08% baseline.

The thresholds were defined before evaluating the simulated experiment result.

---

## 12. Simulated Experiment Events

The experiment used simulated development telemetry.

The following Content ID 14 events were inserted into:

```text
engagement_events
```

with:

```text
source = simulated_experiment
```

Dataset:

```text
Impressions:  20,000
Views:        16,500
Likes:         2,400
Comments:        320
Shares:          500
Saves:           300
Clicks:          460
```

Raw events were independently queried after insertion.

The result confirmed:

```text
click       460
comment     320
impression  20000
like        2400
save        300
share       500
view        16500
```

All records were labelled:

```text
simulated_experiment
```

The dataset must therefore not be represented as real-world social-media performance.

---

## 13. ClickHouse Materialized View Processing

No aggregate performance row was manually inserted.

The raw events flowed through:

```text
engagement_events
        ↓
mv_content_performance_daily
        ↓
content_performance_daily
```

The existing ClickHouse Materialized View automatically aggregated the events.

The resulting Content ID 14 performance row was:

```text
Date:
2026-08-25

Campaign ID:
3

Content ID:
14

Platform:
TikTok

Impressions:
20,000

Views:
16,500

Likes:
2,400

Comments:
320

Shares:
500

Saves:
300

Clicks:
460

CTR:
2.30%

Engagement Rate:
17.60%
```

This independently demonstrated the raw-event → materialized-view → analytical-table pipeline.

---

## 14. Experiment Performance

The experiment result was compared against the TikTok baseline.

### CTR

```text
Baseline:
1.60%

Experiment:
2.30%

Absolute change:
+0.70 percentage points

Relative change:
+43.75%
```

### Engagement Rate

```text
Baseline:
19.08%

Experiment:
17.60%

Absolute change:
-1.48 percentage points
```

The engagement-rate reduction remained inside the predefined 2.00 percentage-point tolerance.

---

## 15. Analytics Agent Evaluation

The Analytics Agent retrieved the experiment performance from ClickHouse and evaluated it against the predefined criteria.

It calculated:

```text
Content ID 14 CTR:
2.30%

Content ID 14 Engagement Rate:
17.60%
```

It evaluated:

```text
CTR > 1.60%
PASS

Engagement >= 17.08%
PASS
```

The Analytics Agent concluded:

```text
Overall Experiment Result:
SUCCESSFUL
```

The agent explicitly stated that the result was based on:

```text
simulated development telemetry
```

and should not be represented as evidence of real-world campaign effectiveness.

---

## 16. Optimisation Agent Evaluation

The completed experiment was then evaluated by the Optimisation Agent.

The agent independently confirmed:

```text
CTR:
2.30%

Baseline CTR:
1.60%

Absolute CTR improvement:
+0.70 percentage points

Relative CTR improvement:
+43.75%
```

It also confirmed:

```text
Experiment engagement:
17.60%

Baseline engagement:
19.08%

Difference:
-1.48 percentage points
```

The Optimisation Agent determined that both predefined success criteria had passed.

It concluded that the original hypothesis was:

```text
SUPPORTED
```

by the available simulated campaign data.

---

## 17. Optimisation Agent Strategic Decision

The Optimisation Agent did not recommend immediate strategy adoption.

Instead it returned:

```text
TEST FURTHER
```

Reason:

- the dataset is simulated;
- the experiment represents a single experimental content item;
- the result should not be treated as statistically definitive;
- further controlled testing should be performed before adopting the strategy more broadly.

This demonstrates appropriate separation between:

```text
Experiment succeeded against predefined criteria
```

and:

```text
Strategy proven in the real world
```

The latter has not been demonstrated.

---

## 18. Proposed Follow-Up Experiment

The Optimisation Agent proposed a larger replication test comparing:

```text
Atmosphere + CTA content
```

against:

```text
standard promotional content
```

The specific sample size and thresholds proposed by the agent should be treated as advisory experimental-design suggestions rather than statistically validated requirements.

A formal statistical power calculation has not been implemented.

---

## 19. Human Approval Boundary Preserved

The Optimisation Agent correctly stopped before making any state-changing action.

It explicitly did not:

- modify Campaign 3;
- create new content;
- update Recommendation ID 1;
- schedule anything;
- publish anything;
- approve its own recommendation.

The agent returned the experiment analysis for human review.

The system therefore preserved the workflow:

```text
Performance
    ↓
Analytics Agent
    ↓
Optimisation Agent
    ↓
Recommendation / interpretation
    ↓
STOP
    ↓
Human decision
```

---

## 20. First Complete Optimisation Loop

Premiere has now demonstrated the following full development loop:

```text
Campaign Content
        ↓
Simulated Engagement Events
        ↓
ClickHouse
        ↓
Materialized View
        ↓
Campaign Performance
        ↓
Analytics Agent
        ↓
Performance Weakness Identified
        ↓
Optimisation Agent
        ↓
Recommendation ID 1
        ↓
Human Approval
        ↓
Content Planner
        ↓
Content ID 14 Experiment
        ↓
Verified Campaign Facts
        ↓
Content Generator
        ↓
Human Approval
        ↓
Review Agent
        ↓
PASS
        ↓
Simulated Experiment Telemetry
        ↓
ClickHouse Materialized View
        ↓
Analytics Agent
        ↓
Experiment SUCCESSFUL
        ↓
Optimisation Agent
        ↓
Hypothesis SUPPORTED
        ↓
Recommendation: TEST FURTHER
        ↓
Human Review
```

This is the first complete evidence-driven optimisation cycle demonstrated by the project.

---

## 21. Why This Milestone Matters

The project has now moved beyond:

```text
Prompt
  ↓
LLM
  ↓
Social Media Post
```

and can demonstrate:

```text
Plan
  ↓
Generate
  ↓
Ground
  ↓
Review
  ↓
Measure
  ↓
Analyse
  ↓
Optimise
  ↓
Experiment
  ↓
Measure Again
  ↓
Learn
```

ClickHouse participates throughout the workflow as:

- operational campaign memory;
- verified campaign-fact storage;
- engagement-event storage;
- materialized performance analytics;
- agent observability;
- optimisation recommendation memory;
- experiment-performance evidence.

---

## 22. Current Recommendation State

The current database record for Recommendation ID 1 remains:

```text
recommendation_id:
1

campaign_id:
3

experiment_content_id:
14

status:
applied_to_plan
```

The existing schema does not yet contain dedicated fields for:

- experiment result;
- baseline CTR;
- experiment CTR;
- engagement baseline;
- experiment engagement;
- outcome;
- follow-up decision;
- evaluated_at.

Therefore the experiment result has been analytically demonstrated but has **not yet been persisted as structured recommendation outcome data**.

This is the next database-design question.

---

## 23. Current Project Position

The first closed-loop optimisation experiment is now functionally complete at the analysis level.

Verified:

```text
[✓] Performance weakness identified
[✓] Optimisation recommendation created
[✓] Human approval preserved
[✓] Recommendation fed back into planning
[✓] Content ID 14 experiment persisted
[✓] Verified campaign facts introduced
[✓] Grounded experiment copy generated
[✓] Review Agent PASS
[✓] Simulated experiment events inserted
[✓] Materialized View aggregation verified
[✓] Experiment CTR calculated
[✓] Experiment engagement calculated
[✓] Analytics Agent evaluation completed
[✓] Optimisation Agent evaluation completed
[✓] Original hypothesis supported by simulated data
[✓] Optimisation Agent stopped for human review
```

Still incomplete:

```text
[ ] Persist structured experiment outcome
[ ] Record recommendation outcome lifecycle
[ ] Build agent_events analytics
[ ] Build final Premiere UI
[ ] Production Google Cloud deployment
[ ] Real social-media data integration
[ ] Native ClickHouse vector retrieval
```

---

## 24. Next Step

The next technical decision is how experiment outcomes should be persisted.

Current Recommendation ID 1 stores:

```text
recommendation
experiment
experiment_content_id
success_metric
status
```

but does not store measured outcomes.

The next implementation should therefore decide between:

1. extending `optimisation_recommendations`; or
2. creating a dedicated experiment-results table.

A dedicated experiment-results model may be preferable because a recommendation can eventually produce multiple experiments.

After that milestone, development can shift toward the Premiere user interface and hackathon demo experience.

---

**Development checkpoint:** Premiere has demonstrated its first complete simulated campaign optimisation and learning loop.


# Development Update: Experiment Outcome Persistence

**Date:** 25 August 2026  
**Project:** Premiere — AI Studio Producer  
**Campaign:** Campaign ID 3 — Shadows of Pretoria  
**Recommendation:** Recommendation ID 1  
**Experiment Content:** Content ID 14  
**Experiment Result:** Experiment Result ID 1

---

## 1. Objective

The objective of this milestone was to persist the measured outcome of the first optimisation experiment as structured ClickHouse data.

The project had already demonstrated:

```text
Performance data
      ↓
Analytics Agent
      ↓
Optimisation Agent
      ↓
Recommendation ID 1
      ↓
Human Approval
      ↓
Content Planner
      ↓
Content ID 14 experiment
      ↓
Content Generation
      ↓
Verified campaign facts
      ↓
Review Agent PASS
      ↓
Simulated experiment telemetry
      ↓
Analytics evaluation
      ↓
Optimisation evaluation
```

However, the experiment result still existed primarily as analytical output.

The goal of this milestone was to give Premiere persistent memory of:

- which recommendation produced the experiment;
- which content item represented the experiment;
- what the baseline was;
- what the experiment achieved;
- whether the predefined success criteria were met;
- and what the next strategic decision should be.

---

## 2. Why a Separate Experiment Result Model Was Introduced

The existing table:

```text
optimisation_recommendations
```

stores the recommendation lifecycle.

For example:

```text
recommendation_id = 1
status = applied_to_plan
experiment_content_id = 14
```

This describes what the system recommended and whether that recommendation was applied to planning.

It does **not** describe the measured outcome of the resulting experiment.

These are separate concepts:

```text
Recommendation Lifecycle
------------------------
proposed
approved
applied_to_plan
```

versus:

```text
Experiment Outcome
------------------
successful
failed
inconclusive
```

A recommendation may also eventually produce more than one experiment.

For this reason, experiment results were separated into their own ClickHouse table.

---

## 3. New ClickHouse Table

A new table was created:

```text
social_producer.experiment_results
```

Schema:

```sql
CREATE TABLE IF NOT EXISTS social_producer.experiment_results
(
    experiment_result_id UInt64,
    recommendation_id UInt64,
    campaign_id UInt64,
    content_id UInt64,
    platform LowCardinality(String),

    baseline_ctr Float64,
    experiment_ctr Float64,
    ctr_change_pp Float64,
    ctr_relative_change_pct Float64,

    baseline_engagement_rate Float64,
    experiment_engagement_rate Float64,
    engagement_change_pp Float64,

    success UInt8,
    outcome LowCardinality(String),
    decision LowCardinality(String),

    data_source LowCardinality(String) DEFAULT 'simulated',
    evaluated_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (
    recommendation_id,
    campaign_id,
    content_id,
    experiment_result_id
);
```

The table was independently verified with:

```sql
DESCRIBE TABLE experiment_results;
```

---

## 4. Experiment Evaluation Function

A new Python database function was introduced:

```python
evaluate_and_save_experiment_result()
```

Its responsibility is to:

1. retrieve experiment performance from ClickHouse;
2. calculate CTR;
3. calculate engagement rate;
4. compare the experiment against its baseline;
5. evaluate success criteria;
6. determine an outcome;
7. persist the result into `experiment_results`.

This is important because experiment results are not manually typed into the database.

Premiere derives them from the same ClickHouse performance data used by the Analytics and Optimisation Agents.

---

## 5. Baseline Handling

The first experiment used the pre-experiment TikTok baseline:

```text
CTR:
1.60%

Engagement Rate:
19.08%
```

The minimum acceptable engagement rate was defined as:

```text
17.08%
```

This represented a maximum tolerated reduction of:

```text
2.00 percentage points
```

from the original TikTok engagement rate.

The success rules were therefore:

```text
CTR > 1.60%

AND

Engagement Rate >= 17.08%
```

The baseline values were supplied explicitly to the evaluation function.

This prevents the experiment from contaminating its own baseline after Content ID 14 becomes part of TikTok campaign performance.

---

## 6. Application-Level Evaluation

The experiment evaluation function was executed for:

```text
Experiment Result ID:
1

Recommendation ID:
1

Campaign ID:
3

Content ID:
14

Platform:
TikTok
```

The function returned:

```text
baseline_ctr:
1.60

experiment_ctr:
2.30

ctr_change_pp:
+0.70

ctr_relative_change_pct:
+43.75

baseline_engagement_rate:
19.08

experiment_engagement_rate:
17.60

engagement_change_pp:
-1.48

minimum_engagement_rate:
17.08

ctr_passed:
True

engagement_passed:
True

success:
True

outcome:
successful

decision:
test_further

data_source:
simulated_experiment
```

---

## 7. Outcome Interpretation

### Click-Through Rate

```text
Baseline CTR:
1.60%

Experiment CTR:
2.30%

Absolute improvement:
+0.70 percentage points

Relative improvement:
+43.75%
```

The CTR criterion passed.

### Engagement Rate

```text
Baseline Engagement Rate:
19.08%

Experiment Engagement Rate:
17.60%

Absolute change:
-1.48 percentage points
```

The experiment remained above the predefined minimum engagement floor of:

```text
17.08%
```

The engagement criterion therefore also passed.

---

## 8. Experiment Outcome

The application classified the experiment as:

```text
success = 1
outcome = successful
decision = test_further
```

This distinction is important.

The experiment was successful **against the predefined development criteria**.

However, the strategic decision remains:

```text
test_further
```

because:

- the telemetry is simulated;
- Content ID 14 represents a single experimental post;
- no real-world audience behaviour has been observed;
- statistical significance has not been established.

The system therefore does not treat one simulated positive result as sufficient evidence for permanent strategy adoption.

---

## 9. Independent ClickHouse Verification

The experiment result was independently queried directly from ClickHouse:

```sql
SELECT *
FROM experiment_results
WHERE experiment_result_id = 1
FORMAT Vertical;
```

The database returned:

```text
experiment_result_id:       1
recommendation_id:          1
campaign_id:                3
content_id:                 14
platform:                   TikTok

baseline_ctr:               1.6
experiment_ctr:             2.3
ctr_change_pp:              0.7
ctr_relative_change_pct:    43.75

baseline_engagement_rate:   19.08
experiment_engagement_rate: 17.6
engagement_change_pp:       -1.48

success:                    1
outcome:                    successful
decision:                   test_further
data_source:                simulated_experiment

evaluated_at:
2026-08-25 16:01:36
```

This independently proves that the experiment result was persisted successfully.

---

## 10. Optimisation Memory Architecture

Premiere now has three separate optimisation memory layers.

### Optimisation Recommendation

```text
optimisation_recommendations
```

Answers:

> What did the system recommend?

Example:

```text
Recommendation ID 1
```

---

### Experiment Content

```text
content_items
```

Answers:

> What campaign experiment was created from the recommendation?

Example:

```text
Content ID 14
```

---

### Experiment Outcome

```text
experiment_results
```

Answers:

> What happened when the experiment was measured?

Example:

```text
Experiment Result ID 1
```

The relationship is:

```text
optimisation_recommendations
        │
        │ recommendation_id = 1
        ▼
content_items
        │
        │ content_id = 14
        ▼
experiment_results
        │
        │ experiment_result_id = 1
        ▼
Measured Outcome
```

---

## 11. Full Closed-Loop State

The project can now demonstrate:

```text
Campaign Content
        ↓
Simulated Engagement
        ↓
ClickHouse
        ↓
Performance Aggregation
        ↓
Analytics Agent
        ↓
Optimisation Agent
        ↓
Recommendation ID 1
        ↓
Human Approval
        ↓
Content Planner
        ↓
Content ID 14 Experiment
        ↓
Verified Campaign Facts
        ↓
Content Generator
        ↓
Human Approval
        ↓
Review Agent PASS
        ↓
Simulated Experiment Events
        ↓
ClickHouse Materialized View
        ↓
Analytics Agent
        ↓
Experiment Evaluation
        ↓
Optimisation Agent
        ↓
Hypothesis Supported
        ↓
Python Experiment Evaluation
        ↓
experiment_results
        ↓
Experiment Result ID 1
        ↓
Decision: TEST FURTHER
        ↓
Human Review
```

This closes the first persistent optimisation-learning loop in Premiere.

---

## 12. Why This Milestone Matters

The system now remembers not only:

```text
What content was created
```

and:

```text
What recommendation was made
```

but also:

```text
What happened after the recommendation was tested
```

That creates a stronger foundation for future agent behaviour.

For example, later agents will be able to query:

```text
Which recommendations succeeded?

Which experiments failed?

Which types of experiments repeatedly improved CTR?

Which recommendations produced unacceptable engagement loss?

Which strategies should be tested again?
```

This moves Premiere closer to evidence-based campaign memory rather than conversation-only reasoning.

---

## 13. Current ClickHouse Role

ClickHouse now supports:

```text
Campaign State
    campaigns

Content State
    content_items

Verified Grounding
    campaign_facts

Raw Performance Events
    engagement_events

Materialized Performance
    content_performance_daily

Optimisation Memory
    optimisation_recommendations

Experiment Outcomes
    experiment_results

Agent Observability
    agent_events
```

The architecture is therefore increasingly centred around ClickHouse as both:

```text
Operational Memory
+
Analytical Memory
+
Agent Observability
+
Optimisation Memory
```

---

## 14. Milestone Status

Completed:

```text
[✓] experiment_results table created
[✓] table schema independently verified
[✓] experiment evaluation function implemented
[✓] experiment performance retrieved from ClickHouse
[✓] CTR calculated programmatically
[✓] engagement rate calculated programmatically
[✓] success criteria evaluated programmatically
[✓] result persisted by Python
[✓] Experiment Result ID 1 created
[✓] independent ClickHouse re-query performed
[✓] persisted values matched application calculation
[✓] Recommendation ID 1 linked to Content ID 14
[✓] Content ID 14 linked to Experiment Result ID 1
[✓] decision persisted as test_further
```

---

## 15. Current Project Position

The first closed-loop optimisation experiment is now complete through persistent outcome storage.

The main backend intelligence path is therefore demonstrated:

```text
Create
  ↓
Measure
  ↓
Analyse
  ↓
Optimise
  ↓
Experiment
  ↓
Measure Again
  ↓
Evaluate
  ↓
Persist Learning
```

The next major development direction is no longer another large backend agent.

The project should now begin exposing this architecture through the **Premiere hackathon UI**.

---

## 16. Next Major Milestone

The next major milestone is:

```text
Premiere User Interface
```

The UI should allow a hackathon reviewer to understand and inspect:

- Campaign 3;
- verified film facts;
- campaign content;
- agent workflow;
- platform analytics;
- Recommendation ID 1;
- Content ID 14;
- baseline vs experiment performance;
- Experiment Result ID 1;
- agent execution/observability data;
- human approval boundaries.

The first UI should focus on demonstrating the already-working backend rather than introducing additional campaign functionality.

---

**Development checkpoint:** Experiment outcomes are now persisted as structured optimisation memory in ClickHouse.

# Development Update: Premiere UI and Live ClickHouse Integration

**Date:** 25 August 2026  
**Project:** Premiere — AI Studio Producer  
**Frontend:** Next.js  
**API:** FastAPI  
**Data Platform:** ClickHouse

---

## 1. Objective

The objective of this milestone was to begin exposing Premiere's already-working backend architecture through a dedicated hackathon user interface.

Until this point, most functionality had been demonstrated through:

```text
Terminal commands
Google ADK Web
ClickHouse queries
Agent traces
Python functions
```

The project now begins presenting those capabilities as a coherent product experience.

The UI is intended to become the visual control room for:

```text
Campaign Management
      ↓
Agent Analysis
      ↓
Optimisation
      ↓
Human Approval
      ↓
Content Production
      ↓
Experimentation
      ↓
Measurement
      ↓
Learning
```

---

## 2. Frontend Technology Decision

The frontend was created using:

```text
Next.js 16.3.3
React
TypeScript
Tailwind CSS
App Router
Turbopack
```

The application was created inside:

```text
frontend/
```

using:

```bash
npx create-next-app@latest frontend
```

The recommended Next.js defaults were selected.

The resulting project structure includes:

```text
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── public/
├── package.json
├── next.config.ts
└── ...
```

---

## 3. Local Frontend Runtime

The frontend is currently run locally with:

```bash
cd frontend
npm run dev
```

The development server runs at:

```text
http://localhost:3000
```

Next.js successfully started using:

```text
Next.js 16.3.3
Turbopack
```

The initial starter page loaded successfully.

---

## 4. Premiere UI Direction

The hackathon UI is being designed as an:

```text
AI Studio Control Room
```

rather than only as a conventional analytics dashboard.

The goal is to allow judges to visually follow the agent workflow:

```text
Analyse
   ↓
Recommend
   ↓
Human Review
   ↓
Plan
   ↓
Generate
   ↓
Review
   ↓
Experiment
   ↓
Measure
   ↓
Learn
```

The intended major UI modules are:

```text
Overview
Insights
Content
Experiments
Activity
```

---

## 5. Initial Dashboard Shell

The first Premiere dashboard shell was implemented in:

```text
frontend/app/page.tsx
```

The first version displayed:

- Premiere branding;
- Campaign 3;
- Ubuntu Frame Studios;
- Shadows of Pretoria;
- campaign objective;
- campaign audience;
- campaign duration;
- campaign status;
- platform-performance cards;
- campaign optimisation information;
- agent-team information.

The initial performance values were temporarily hard-coded only to establish the visual structure and information hierarchy.

---

## 6. Python API Layer Introduced

To replace hard-coded UI data with real project state, a lightweight API layer was introduced using:

```text
FastAPI
```

The API is defined in:

```text
social_producer/api.py
```

and runs locally using:

```bash
uvicorn social_producer.api:app --reload --port 8001
```

The API is available at:

```text
http://localhost:8001
```

---

## 7. API Architecture

The current UI data path is:

```text
Premiere Next.js UI
        ↓
FastAPI
        ↓
database.py
        ↓
clickhouse-connect
        ↓
ClickHouse
```

This API path is separate from the existing agent-facing MCP integration.

The full architecture remains:

```text
Premiere Next.js UI
        ↓
FastAPI / Application API
        ↓
Python / Google ADK
        ↓
Premiere Director + Specialist Agents
        │
        ├──────────── Agent Read Path ────────────┐
        │                                         │
        ▼                                         ▼
ADK MCPToolset                            Controlled Python Tools
        ↓                                         ↓
official mcp-clickhouse                   database.py
        ↓                                         ↓
        └──────────────────┬──────────────────────┘
                           ↓
                       ClickHouse
```

MCP remains an important part of agent-to-ClickHouse access.

The ordinary UI does not need to use MCP for every application read.

---

## 8. Initial API Endpoints

The initial FastAPI layer exposes read-only endpoints including:

```text
GET /health

GET /campaigns/{campaign_id}

GET /campaigns/{campaign_id}/facts

GET /campaigns/{campaign_id}/performance

GET /campaigns/{campaign_id}/platforms

GET /content/{content_id}
```

The health endpoint successfully returned:

```json
{
  "status": "ok"
}
```

---

## 9. Campaign 3 API Verification

The API successfully retrieved Campaign ID 3.

Returned data included:

```text
campaign_id:
3

brand_name:
Ubuntu Frame Studios

objective:
Build awareness and audience engagement leading up to the premiere.

target_audience:
African film audiences aged 18 to 35

platforms:
Instagram
TikTok
Facebook
YouTube

duration_days:
28

status:
draft
```

This verified:

```text
Next application layer
        ↓
FastAPI
        ↓
database.py
        ↓
ClickHouse campaigns table
```

---

## 10. FastAPI / ClickHouse Concurrency Issue

The first call to:

```text
GET /campaigns/3/platforms
```

returned:

```text
500 Internal Server Error
```

The underlying ClickHouse error was:

```text
Attempt to execute concurrent queries within the same session.
Please use a separate client instance per thread/process.
```

The issue was caused by the existing global `clickhouse-connect` client using automatically generated session state while FastAPI executed requests in worker threads.

The existing backend had largely operated sequentially, so this concurrency issue had not previously appeared.

---

## 11. ClickHouse Client Concurrency Fix

The shared ClickHouse client configuration was updated with:

```python
autogenerate_session_id=False
```

This removed unnecessary shared session state.

The architecture could therefore continue using the shared application client without introducing a new ClickHouse connection for every individual API call.

After restarting FastAPI, the platform endpoint worked successfully.

This demonstrated another runtime lesson:

```text
Sequential application behaviour
        ≠
Concurrent web API behaviour
```

---

## 12. Live Platform Performance API

After the concurrency fix, the following endpoint worked:

```text
GET /campaigns/3/platforms
```

The API returned live Campaign 3 performance directly from ClickHouse.

Current platform data included:

### TikTok

```text
Impressions:
102,400

Views:
85,700

Clicks:
1,780

Engagement Rate:
18.79%

Click Rate:
1.74%
```

### Instagram

```text
Impressions:
42,520

Views:
24,130

Clicks:
1,236

Engagement Rate:
11.35%

Click Rate:
2.91%
```

### YouTube

```text
Impressions:
39,100

Views:
25,600

Clicks:
870

Engagement Rate:
8.42%

Click Rate:
2.23%
```

### Facebook

```text
Impressions:
9,100

Views:
3,900

Clicks:
142

Engagement Rate:
6.18%

Click Rate:
1.56%
```

---

## 13. Important Baseline Distinction

TikTok originally had a pre-experiment baseline of:

```text
Impressions:
82,400

CTR:
1.60%

Engagement Rate:
19.08%
```

After Content ID 14 experiment telemetry was added, the current TikTok aggregate became:

```text
Impressions:
102,400

CTR:
1.74%

Engagement Rate:
18.79%
```

This difference is expected.

The UI therefore needs to distinguish between:

```text
Current Campaign Performance
```

and:

```text
Historical Experiment Baseline
```

The experiment baseline must not be recalculated from the current TikTok aggregate.

The historical baseline remains preserved in:

```text
experiment_results
```

---

## 14. First Live UI Data Path

The Next.js page was updated to fetch Campaign 3 and platform performance from FastAPI.

The live browser path became:

```text
Next.js
   ↓
fetch()
   ↓
FastAPI
   ↓
database.py
   ↓
clickhouse-connect
   ↓
ClickHouse
```

The Premiere browser UI successfully rendered:

```text
Campaign 3

Ubuntu Frame Studios

African film audiences aged 18 to 35

28 days

draft
```

and the current platform metrics directly from ClickHouse.

---

## 15. Live TikTok Verification in UI

The browser displayed:

```text
TikTok

102,400 impressions

Engagement:
18.79%

CTR:
1.74%

1,780 clicks
85,700 views
```

These values differ from the earlier hard-coded baseline.

This independently demonstrates that the UI is now rendering current application data rather than static demo constants.

---

## 16. AI Insights Interface

A new:

```text
Insights
```

module was introduced.

The UI contains an:

```text
Analyse Campaign
```

interaction.

The current visual sequence is:

```text
Analytics Agent
      ↓
Platform Analysis
      ↓
Optimisation Agent
      ↓
Recommendation
```

The first version uses short frontend timing transitions to visualise the intended agent workflow.

This is currently a UI simulation of the sequence.

It must not yet be represented as a real-time ADK agent invocation from the UI.

A later milestone will connect this interaction to the actual agent runtime.

---

## 17. Control-Room Navigation

The current navigation includes:

```text
Overview

Insights

Content

Experiments

Activity
```

These modules correspond to the intended hackathon demonstration flow.

### Overview

Shows:

- campaign information;
- current live platform analytics.

### Insights

Shows:

- campaign-analysis workflow;
- optimisation recommendation.

### Content

Planned to show:

- planned content;
- generated drafts;
- review outcomes;
- approval lifecycle.

### Experiments

Planned to show:

- Recommendation ID 1;
- Content ID 14;
- Experiment Result ID 1;
- baseline vs experiment performance.

### Activity

Planned to show:

- agent execution;
- MCP calls;
- tool execution;
- agent_events telemetry.

---

## 18. Optimisation Recommendation API

A new API endpoint was introduced:

```text
GET /recommendations/{recommendation_id}
```

Recommendation ID 1 was successfully retrieved directly from ClickHouse.

The API returned:

```text
recommendation_id:
1

campaign_id:
3

recommendation_type:
platform_experiment

experiment_content_id:
14

status:
applied_to_plan
```

It also returned the complete stored:

- observation;
- hypothesis;
- recommendation;
- experiment;
- success metric;
- creation time.

---

## 19. Recommendation ID 1 Retrieved

The returned recommendation contains:

### Observation

```text
TikTok generated 82,400 impressions and 69,200 views
with a 19.08% engagement rate, but its click rate was 1.60%.
```

### Hypothesis

```text
Adding a stronger action-oriented CTA to a high-engagement
TikTok format may increase click-through performance.
```

### Recommendation

```text
Test a CTA-oriented TikTok post while preserving the
behind-the-scenes or atmosphere format that performed strongly.
```

### Experiment

```text
Create a TikTok experiment combining a high-engagement creative
format with an explicit verified campaign CTA.
```

### Experiment Content

```text
Content ID:
14
```

### Status

```text
applied_to_plan
```

---

## 20. UI Lifecycle Correction

The first Insights UI showed:

```text
Reject

Approve Experiment
```

for Recommendation ID 1.

This was inconsistent with the actual ClickHouse state because Recommendation ID 1 had already progressed to:

```text
status = applied_to_plan
```

and had already created:

```text
experiment_content_id = 14
```

The UI was therefore corrected to reflect the persistent application state.

The updated recommendation card displays:

```text
Recommendation #1

Status:
APPLIED TO PLAN

Experiment:
Content ID 14
```

rather than presenting an approval decision that had already happened.

This establishes an important UI principle:

```text
Visible workflow state
        =
Persistent backend state
```

wherever possible.

---

## 21. Updated Insights Architecture

The Insights module now combines:

```text
Current campaign-performance visualisation
        +
Persisted optimisation recommendation
        +
Recommendation lifecycle state
        +
Experiment relationship
```

The workflow shown to the user is:

```text
Campaign 3
        ↓
Campaign Analysis
        ↓
Recommendation #1
        ↓
status = applied_to_plan
        ↓
Content ID 14
        ↓
View Experiment
```

---

## 22. Current UI Status

Completed:

```text
[✓] Next.js frontend created
[✓] TypeScript enabled
[✓] Tailwind CSS enabled
[✓] App Router enabled
[✓] Local frontend running
[✓] Premiere dashboard shell created
[✓] Overview navigation created
[✓] Insights navigation created
[✓] Content navigation placeholder created
[✓] Experiments navigation placeholder created
[✓] Activity navigation placeholder created
[✓] FastAPI installed
[✓] Premiere API created
[✓] API health endpoint working
[✓] Campaign 3 API working
[✓] Platform performance API working
[✓] FastAPI concurrency bug identified
[✓] ClickHouse session fix implemented
[✓] Live campaign data rendered in Next.js
[✓] Live platform analytics rendered in Next.js
[✓] Recommendation API created
[✓] Recommendation ID 1 retrieved from ClickHouse
[✓] Recommendation lifecycle shown in UI
[✓] Content ID 14 relationship exposed
```

Still to implement:

```text
[ ] Real ADK agent invocation from UI
[ ] Experiment Result API
[ ] Full Experiments screen
[ ] Content lifecycle screen
[ ] Agent Activity screen
[ ] agent_events API
[ ] MCP activity visualisation
[ ] Human approval interaction for new recommendations
[ ] Final architecture screen
[ ] Production deployment
```

---

## 23. Current Product Architecture

The working local product architecture is now:

```text
                    User
                     │
                     ▼
            Premiere Next.js UI
                     │
                     ▼
                FastAPI
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
   Application Reads      Google ADK Runtime
          │                     │
          ▼                     │
      database.py               ├── Content Planner
          │                     ├── Content Generator
          ▼                     ├── Review Agent
 clickhouse-connect             ├── Analytics Agent
          │                     └── Optimisation Agent
          │                           │
          │                           ▼
          │                       MCPToolset
          │                           │
          │                           ▼
          │                     mcp-clickhouse
          │                           │
          └─────────────┬─────────────┘
                        ▼
                    ClickHouse
```

The UI currently uses the application API read path.

The agent runtime continues to use the official MCP integration where appropriate.

---

## 24. Hackathon Demo Direction

The UI is being designed specifically to demonstrate Premiere in action.

The intended video sequence is:

```text
Campaign Overview
      ↓
Analyse Campaign
      ↓
Analytics Agent
      ↓
Optimisation Recommendation
      ↓
Human Approval
      ↓
Experiment Content
      ↓
Grounded Generation
      ↓
Review
      ↓
Experiment Telemetry
      ↓
ClickHouse
      ↓
Experiment Result
      ↓
Optimisation Learning
```

The UI should therefore make the system feel like:

```text
an AI studio team operating a campaign
```

rather than simply:

```text
an analytics dashboard
```

---

## 25. Next UI Milestone

The next module to implement is:

```text
Experiments
```

It should retrieve:

```text
Recommendation ID 1

Content ID 14

Experiment Result ID 1
```

from the backend.

The primary visual should show:

```text
TikTok CTR

Baseline:
1.60%

        ↓

Experiment:
2.30%

Relative uplift:
+43.75%
```

alongside:

```text
Engagement

Baseline:
19.08%

Experiment:
17.60%

Minimum accepted:
17.08%
```

and:

```text
Outcome:
SUCCESSFUL

Decision:
TEST FURTHER
```

This will become one of the strongest visual moments in the hackathon demonstration.

---

**Development checkpoint:** Premiere now has a working Next.js control-room interface reading real Campaign 3 and optimisation data from ClickHouse through FastAPI.
