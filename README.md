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

````markdown
## ClickHouse Integration

ClickHouse is being introduced as the main data and analytics platform for the
AI Social Media Producer.

The first version of the project stored campaign information temporarily in
Python memory. This worked for testing the agent workflow, but the data was
lost whenever the application restarted.

ClickHouse is now being used to provide persistent storage and will later be
used for campaign analytics, engagement events and agent activity.

### Local Development Setup

During development, ClickHouse runs locally inside Docker.

The ClickHouse container exposes two main ports:

- `8123` - HTTP interface used by the Python application
- `9000` - native ClickHouse protocol used by `clickhouse-client`

The development database is:

```text
social_producer
````

A dedicated ClickHouse user is also used by the application instead of relying
on the default ClickHouse user.

### Campaigns Table

The first table created for the project is:

```text
campaigns
```

It was created using:

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

### Why MergeTree?

The `campaigns` table uses the ClickHouse `MergeTree` engine.

MergeTree is designed for storing and querying analytical data efficiently.

This project will make greater use of MergeTree as more event-based data is
introduced, particularly social media engagement events and agent activity.

### Sorting Key

The table uses:

```sql
ORDER BY (brand_name, campaign_id)
```

In a ClickHouse MergeTree table, `ORDER BY` is more than a way of sorting the
final query output.

It defines the sorting key used to organise the stored data.

For the initial campaigns table, `brand_name` appears first because campaigns
will commonly be retrieved and analysed by brand.

### Array Data Type

Campaign platforms are stored using:

```sql
platforms Array(String)
```

This allows a campaign to contain several platforms in one field.

For example:

```text
['Facebook', 'LinkedIn']
```

### LowCardinality

Campaign status uses:

```sql
status LowCardinality(String)
```

Campaigns are expected to repeatedly use a small set of values such as:

```text
draft
approved
scheduled
active
completed
cancelled
```

This makes `LowCardinality(String)` suitable for the status field.

---

## Python and ClickHouse Connection

The Python application connects to ClickHouse using `clickhouse-connect`.

The current development flow is:

```text
Python Application
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
social_producer database
        |
        v
campaigns table
```

Database configuration is stored in environment variables rather than being
hard-coded into the Python source code.

The `.env` file contains development settings such as:

```text
CLICKHOUSE_HOST
CLICKHOUSE_PORT
CLICKHOUSE_USER
CLICKHOUSE_PASSWORD
CLICKHOUSE_DATABASE
```

The `.env` file is excluded from Git because it contains credentials.

The environment file is loaded explicitly from the `social_producer`
directory:

```python
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)
```

The ClickHouse connection was successfully tested from Python and returned
the server version:

```text
26.7.4.58
```

---

## ClickHouse Troubleshooting and Lessons Learned

Several problems were encountered while setting up ClickHouse. These problems
helped clarify how Docker, ClickHouse and the Python application interact.

### 1. Table Created in the Wrong Database

The first `campaigns` table was accidentally created inside the ClickHouse
`default` database instead of the project's `social_producer` database.

When attempting to insert data, ClickHouse returned an error indicating:

```text
Table social_producer.campaigns does not exist.
Maybe you meant default.campaigns?
```

The problem was fixed by selecting the correct database before creating the
table:

```sql
USE social_producer;
```

The table was then recreated inside the correct database.

#### What I learned

Creating a database does not automatically make it the active database.

Tables can also be referenced using their complete name:

```text
social_producer.campaigns
```

This can prevent accidentally querying or creating objects in the wrong
database.

---

### 2. ClickHouse Authentication Error

The first Python connection attempted to use the ClickHouse `default` user
without a password.

ClickHouse rejected the connection with an authentication error.

The Docker environment was recreated with a dedicated application user and
password.

The application now connects using the `social_producer` ClickHouse user.

#### What I learned

The application and command-line client can connect to ClickHouse through
different interfaces.

The Python application currently communicates with ClickHouse through the HTTP
interface on port `8123`.

The ClickHouse command-line client normally uses the native ClickHouse protocol
on port `9000`.

A successful command-line connection therefore does not automatically prove
that the application's HTTP connection is configured correctly.

---

### 3. Docker Container Was Running but ClickHouse Was Not Ready

At one stage:

```bash
docker ps
```

showed the ClickHouse container as running, but attempts to connect to the
database failed.

The ClickHouse logs showed port binding problems involving ports `8123` and
`9000`.

The container process and logs were investigated using commands such as:

```bash
docker top clickhouse-server
```

and:

```bash
docker logs clickhouse-server
```

After the initial user and database setup had completed, restarting the
container allowed ClickHouse to start normally.

#### What I learned

A Docker container being marked as `Up` does not necessarily mean that the
application running inside it is ready.

The service itself must also be checked.

Container logs are therefore important when diagnosing database startup and
network problems.

---

### 4. Environment Variables Were Not Loading

After moving the ClickHouse credentials from Python into `.env`, authentication
started failing again.

ClickHouse reported that the application was trying to authenticate as the
`default` user.

The problem was that the `.env` file was located inside:

```text
social_producer/.env
```

while the application was being started from the project root.

The environment file is now loaded using an explicit path:

```python
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)
```

The configuration was tested without displaying the password.

#### What I learned

Environment variables should not be assumed to have loaded successfully.

Configuration can be tested separately from the database connection.

Database passwords and API keys should also remain outside source code and
should never be committed to a public Git repository.

---

### 5. Python Client Scope Error

While restructuring `database.py`, the following error occurred:

```text
NameError: name 'client' is not defined
```

This was a Python scope problem rather than a ClickHouse problem.

The ClickHouse client needs to be available to all database functions that
use the connection.

The database module currently provides functions for:

```text
test_connection()
get_next_campaign_id()
create_campaign_record()
get_campaigns()
```

#### What I learned

Application errors and database errors should be diagnosed separately.

A failed database-related function does not necessarily mean that the database
server itself has failed.

---

### 6. Database Objects Were Lost When the Container Was Recreated

The original ClickHouse container was removed while fixing the authentication
configuration.

After creating the new container, Python successfully connected to ClickHouse
but returned an `UNKNOWN_TABLE` error when querying `campaigns`.

The table had disappeared because it belonged to the previous container.

The `campaigns` table was recreated.

#### What I learned

The current Docker setup does not yet use a dedicated persistent volume.

Removing the ClickHouse container can therefore remove the development database
state.

A persistent Docker volume will be added so that ClickHouse data survives
container replacement.

---

## First Successful Campaign Insert

After resolving the connection and configuration problems, campaign data was
successfully inserted into ClickHouse from Python.

The first successful record contained:

```text
Campaign ID:       1
Brand:             BePlugged Tech
Objective:         Generate web development leads
Target Audience:   Small businesses in South Africa
Platforms:         Facebook, LinkedIn
Duration:          14 days
Status:            draft
```

The record was then successfully retrieved from ClickHouse using Python.

This confirmed the working data path:

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

## Current ClickHouse Status

Completed:

* ClickHouse running locally with Docker
* Dedicated `social_producer` database
* Dedicated ClickHouse application user
* `campaigns` MergeTree table
* Python-to-ClickHouse connection
* Environment-based database configuration
* Python campaign insert
* Python campaign retrieval

Next:

* Add a persistent Docker volume
* Connect the ADK `create_campaign` tool to ClickHouse
* Allow the agent to retrieve stored campaigns
* Introduce campaign content tables
* Introduce engagement event storage
* Build ClickHouse analytics queries
* Add materialized views where appropriate
* Integrate the ClickHouse MCP server

