# Premiere — AI Studio Producer

**Premiere** is a human-governed multi-agent AI system for planning, producing, reviewing, analysing and optimising independent-film release campaigns.

Built for the **Google Cloud / Gemini Agentic Cinema Hackathon**, Premiere combines **Google Gemini**, **Google Agent Development Kit (ADK)**, **Python**, **ClickHouse**, and the **official ClickHouse MCP server**.

Instead of treating AI as a single chatbot that generates social-media posts, Premiere models campaign production as a coordinated studio workflow involving specialised agents, persistent campaign state, performance analytics, human approval boundaries and an optimisation feedback loop.

> **Premiere doesn't just generate campaign content. It learns from campaign performance and uses that evidence to inform what should be produced next.**

---

## Why Premiere?

Independent film campaigns involve more than writing captions.

A release team needs to:

- understand the film and its verified promotional facts;
- design a campaign;
- plan content across multiple platforms;
- generate platform-specific copy;
- review content for unsupported claims;
- approve consequential actions;
- measure audience response;
- identify what is working;
- propose improvements;
- test those improvements; and
- learn from the results.

Premiere is being designed around that complete lifecycle.

```text
Plan
 ↓
Generate
 ↓
Review
 ↓
Human Approve
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

---

# Architecture

```text
                              USER
                                │
                                ▼
                    ┌──────────────────────┐
                    │  Premiere Director   │
                    │   Root Orchestrator  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
      Content Planner    Content Generator   Review Agent
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                         Human Approval
                               │
                               ▼
                          ClickHouse
                               │
               ┌───────────────┴───────────────┐
               │                               │
               ▼                               ▼
        Engagement Events                 Agent Events
               │                               │
               ▼                               ▼
       Materialized Views               Observability
               │
               ▼
         Analytics Agent
               │
               ▼
       Optimisation Agent
               │
               ▼
      Optimisation Recommendation
               │
               ▼
         Human Approval
               │
               └──────────────────────► Content Planner
                                         │
                                         ▼
                                      Experiment
```

The root Director coordinates specialist agents and controls consequential application writes.

Specialist agents primarily reason, retrieve data and make recommendations.

---

# Current Agent Team

| Agent | Responsibility | Status |
|---|---|---|
| Premiere Director | Root orchestration and approval-controlled actions | ✅ |
| Content Planning Agent | Determines what campaign content should be created | ✅ |
| Content Generation Agent | Generates platform-specific draft copy | ✅ |
| Review Agent | Checks grounding, alignment and content quality | ✅ |
| Analytics Agent | Analyses campaign-performance data | ✅ |
| Optimisation Agent | Converts performance evidence into optimisation recommendations | ✅ |

The Analytics and Optimisation Agent runtime paths have been independently verified through Google ADK execution traces.

---

# Human-in-the-Loop Design

Premiere separates:

```text
AI reasoning
```

from:

```text
Consequential state changes
```

Agents do not receive unrestricted authority to change campaign state.

## Campaign creation

```text
Campaign Proposal
       ↓
Human Approval
       ↓
Campaign persisted
```

## Content planning

```text
Content Plan
       ↓
Human Approval
       ↓
status = planned
```

## Content generation

```text
Generated Draft
       ↓
Human Approval
       ↓
status = draft
```

## Review

```text
Review Agent
       ↓
PASS / REVISE / BLOCKED
       ↓
NO automatic state change
```

## Optimisation

```text
Performance Evidence
       ↓
Optimisation Agent
       ↓
Recommendation
       ↓
Human Approval
       ↓
Planner may use recommendation
```

A recommendation from an agent is therefore not equivalent to permission to modify application state.

---

# Development Film Scenario

Premiere currently uses a controlled fictional development scenario.

## Studio

```text
Ubuntu Frame Studios
```

## Film

```text
Shadows of Pretoria
```

Verified development facts:

| Field | Value |
|---|---|
| Genre | Crime drama |
| Premiere | 20 October 2026 |
| Primary Market | South Africa |
| Audience | African film audiences aged 18–35 |
| Platforms | Instagram, TikTok, Facebook, YouTube |

These values are fictional test data.

Agents must not infer additional film facts from this metadata.

For example:

```text
Title contains "Pretoria"
        ≠
Verified setting is Pretoria
```

No cast, characters, plot, venue, ticket information, awards, reviews, distribution method or promotional assets should be assumed unless explicitly supplied.

---

# Grounding

Grounding is a core design requirement.

Premiere distinguishes between:

```text
VERIFIED INFORMATION
```

and:

```text
REQUIRES STUDIO INFORMATION
REQUIRES STUDIO ASSET
UNSUPPORTED CLAIM
```

Testing has deliberately attempted to make agents invent information.

For example, a test draft claimed:

```text
BePlugged Tech has helped over 10,000 South African learners
secure high-paying IT jobs.
```

The Review Agent correctly returned:

```text
BLOCKED
```

because those claims were unsupported.

Film-specific testing also exposed incorrect inference of a Pretoria setting from the title *Shadows of Pretoria*. Agent instructions were subsequently strengthened.

Grounding must apply not only to generated content but also to:

- planning;
- review reasoning;
- suggested rewrites;
- optimisation hypotheses;
- recommendations; and
- proposed experiments.

A recent optimisation test, for example, proposed a `"Buy Tickets Now"` experiment despite ticket availability not being part of the verified film information. This remains a known grounding improvement.

---

# ClickHouse as the Data and Analytics Layer

ClickHouse is not used merely as a database.

It currently serves several architectural roles.

```text
                         ClickHouse
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
 Operational State      Campaign Analytics    AI Observability
        │                     │                     │
 campaigns          engagement_events         agent_events
 content_items              │
 optimisation_              ▼
 recommendations     Materialized View
                            │
                            ▼
                content_performance_daily
```

This allows ClickHouse to act as:

1. persistent campaign memory;
2. event storage;
3. campaign analytics infrastructure;
4. multi-agent observability infrastructure; and
5. persistent optimisation memory.

---

# Current ClickHouse Data Model

Important application datasets include:

```text
campaigns
content_items
engagement_events
content_performance_daily
agent_events
optimisation_recommendations
```

## Campaign state

```text
campaigns
    │
    │ 1:N
    ▼
content_items
```

## Performance events

```text
content_items
      │
      ▼
engagement_events
      │
      ▼
mv_content_performance_daily
      │
      ▼
content_performance_daily
```

The performance roll-up uses:

```text
SummingMergeTree
```

to maintain aggregated campaign metrics.

---

# ClickHouse MCP Integration

Premiere integrates Google ADK with the **official ClickHouse MCP server**.

The verified read path is:

```text
User
 ↓
Gemini
 ↓
Google ADK
 ↓
Premiere Director
 ↓
McpToolset
 ↓
official mcp-clickhouse
 ↓
ClickHouse
 ↓
Grounded response
```

The MCP integration exposes:

```text
list_databases
list_tables
run_query
```

MCP is currently configured as:

```text
READ ONLY
```

with:

```text
CLICKHOUSE_ALLOW_WRITE_ACCESS=false
```

Consequential writes continue through controlled application tools and human approval boundaries.

---

# Verified Agent-Driven MCP Execution

Campaign ID 3 was queried through the real Premiere Director.

The ADK execution trace showed an actual:

```text
run_query
```

tool invocation through the ClickHouse MCP integration.

The returned data matched the independently verified ClickHouse state.

This proves:

```text
Director Agent
      ↓
Google ADK
      ↓
MCPToolset
      ↓
run_query
      ↓
mcp-clickhouse
      ↓
ClickHouse
```

rather than merely demonstrating a standalone MCP client.

---

# Agent Observability

Premiere also records agent execution telemetry in:

```text
agent_events
```

The observability layer captures information such as:

- session;
- agent;
- tool;
- event type;
- status;
- error information;
- latency;
- model;
- grounding result;
- campaign/content identifiers where available;
- token telemetry where available.

The architecture is:

```text
Agent / Tool Execution
        ↓
Google ADK Callbacks
        ↓
Event Logger
        ↓
ClickHouse
        ↓
agent_events
```

Live MCP execution has already generated automatic telemetry for:

```text
list_databases
list_tables
run_query
```

including measured execution latency.

Campaign analytics and agent observability remain intentionally separate:

```text
Campaign Analytics
=
How well is the campaign performing?

Agent Observability
=
How well is the AI system performing?
```

Both are backed by ClickHouse.

---

# Campaign Performance Analytics

Campaign ID 3 uses a simulated engagement dataset for development and demonstration.

It must not be represented as real production social-media performance.

Current platform results:

| Platform | Impressions | Views | Clicks | Engagement Rate | CTR |
|---|---:|---:|---:|---:|---:|
| TikTok | 82,400 | 69,200 | 1,320 | 19.08% | 1.60% |
| Instagram | 42,520 | 24,130 | 1,236 | 11.35% | 2.91% |
| YouTube | 39,100 | 25,600 | 870 | 8.42% | 2.23% |
| Facebook | 9,100 | 3,900 | 142 | 6.18% | 1.56% |

The system correctly distinguishes between optimisation objectives.

For example:

```text
TikTok
→ strongest reach and engagement

Instagram
→ strongest click-through efficiency

Facebook
→ weakest current performance
```

The Analytics Agent's runtime execution was independently verified through an ADK trace.

The trace showed:

```text
invoke_agent analytics_agent
        │
        ├── get_campaign_performance(campaign_id=3)
        │
        └── get_platform_performance(campaign_id=3)
```

Both tools returned real Campaign 3 performance data.

---

# Closed-Loop Optimisation

Premiere's most important current workflow is its optimisation feedback loop.

```text
Campaign Content
       ↓
Engagement Events
       ↓
ClickHouse
       ↓
Performance Aggregation
       ↓
Analytics Agent
       ↓
Optimisation Agent
       ↓
Recommendation
       ↓
Human Approval
       ↓
Content Planner
       ↓
Experimental Content
       ↓
Measure Again
```

The Optimisation Agent does not directly modify campaigns.

It structures recommendations into:

1. observations;
2. hypotheses;
3. recommendations;
4. experiments; and
5. success metrics.

Its runtime execution has also been independently verified through an ADK trace:

```text
optimisation_agent
       │
       ├── get_campaign_performance(campaign_id=3)
       │
       └── get_platform_performance(campaign_id=3)
```

---

# First Optimisation Feedback Loop

Campaign 3 generated the project's first persisted optimisation recommendation.

```text
Recommendation ID: 1
Campaign ID:       3
```

The evidence showed that TikTok generated:

```text
82,400 impressions
69,200 views
19.08% engagement rate
1.60% CTR
```

The approved optimisation direction was to test whether a stronger action-oriented CTA could improve TikTok click-through performance while preserving its strong engagement behaviour.

The baseline success threshold is:

```text
TikTok CTR > 1.60%
```

---

# Recommendation → Experiment

The approved recommendation was fed back into the Content Planning Agent.

The planner proposed:

```text
Platform:
TikTok

Content Type:
experiment

Topic:
TikTok Atmosphere & Premiere Reminder Experiment

Campaign Day:
19
```

Purpose:

```text
Test whether combining TikTok's high-engagement atmosphere
format with an explicit verified premiere-date call-to-action
can increase click-through performance above the current
TikTok baseline.
```

After human approval, the experiment was persisted as:

```text
Content ID: 14
Campaign ID: 3
Status: planned
```

An independent Python/ClickHouse re-query confirmed:

```text
content_id       = 14
campaign_id      = 3
platform         = TikTok
content_type     = experiment
campaign_day     = 19
status           = planned
content_text     = ""
scheduled_at     = None
```

This closes the feedback loop from performance evidence to persistent future campaign action.

The experiment outcome has **not yet been measured**.

---

# Current Demonstrated Workflow

Premiere has now demonstrated:

```text
Film Brief
    ↓
Director
    ↓
Campaign Proposal
    ↓
Human Approval
    ↓
ClickHouse
    ↓
Content Planner
    ↓
Human Selective Approval
    ↓
Planned Content
    ↓
Content Generator
    ↓
Human Approval
    ↓
Draft
    ↓
Review Agent
    ↓
PASS / BLOCKED
    ↓
Engagement Events
    ↓
ClickHouse Analytics
    ↓
Analytics Agent
    ↓
Optimisation Agent
    ↓
Recommendation
    ↓
Human Approval
    ↓
Planner Feedback
    ↓
Experiment
```

This is substantially different from:

```text
Prompt → LLM → social-media post
```

---

# Implementation Status

| Capability | Status |
|---|---|
| Gemini integration | ✅ |
| Google ADK root orchestration | ✅ |
| Content Planning Agent | ✅ |
| Content Generation Agent | ✅ |
| Review Agent | ✅ |
| Analytics Agent | ✅ |
| Optimisation Agent | ✅ |
| Human approval boundaries | ✅ |
| Campaign persistence | ✅ |
| Content persistence | ✅ |
| ClickHouse MergeTree storage | ✅ |
| Engagement event model | ✅ |
| Materialized performance aggregation | ✅ |
| Campaign analytics | ✅ |
| Official ClickHouse MCP | ✅ |
| Agent-driven MCP query | ✅ |
| `agent_events` observability | ✅ |
| MCP latency telemetry | ✅ |
| Persistent optimisation recommendations | ✅ |
| Approved recommendation → planner feedback | ✅ |
| Experimental Content ID 14 persistence | ✅ |
| Independent Content ID 14 verification | ✅ |
| Content ID 14 performance measurement | ⏳ |
| Experiment vs baseline analysis | ⏳ |
| Real social-platform publishing | ❌ |
| Production Google Cloud deployment | ⏳ |
| Vector asset retrieval | ⏳ |

---

# Technology Stack

Premiere currently uses:

- Python
- Google Gemini
- Google Agent Development Kit (ADK)
- ClickHouse
- `clickhouse-connect`
- official `mcp-clickhouse`
- Model Context Protocol
- Docker
- `uv`

Development has used:

```text
google-adk 2.7.1
mcp 1.29.0
```

The local ClickHouse development environment has been tested against:

```text
ClickHouse 26.7.4.58
```

---

# Local Development

## Clone

```bash
git clone git@github.com:geraldrush/social-director.git
cd social-director
```

## Create environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment configuration

Create:

```text
social_producer/.env
```

Example:

```dotenv
GOOGLE_API_KEY=your_google_api_key

CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=social_producer
CLICKHOUSE_PASSWORD=your_clickhouse_password
CLICKHOUSE_DATABASE=social_producer
```

Never commit real credentials.

---

# Local ClickHouse

Create persistent storage:

```bash
docker volume create clickhouse-data
```

Run ClickHouse:

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

The application uses:

```text
8123 → HTTP / clickhouse-connect
9000 → native ClickHouse protocol
```

---

# Test ClickHouse

```bash
python -c "from social_producer.database import test_connection; print(test_connection())"
```

A successful development environment should return the running ClickHouse version.

---

# Run Premiere

Activate the environment:

```bash
source .venv/bin/activate
```

Then:

```bash
adk web
```

Select:

```text
social_producer
```

The internal Python package retains the original `social_producer` name from the project's earlier generic social-media prototype.

The product itself is now:

```text
Premiere — AI Studio Producer
```

---

# Security

Never commit:

```text
.env
.venv/
API keys
ClickHouse passwords
Google credentials
service-account credentials
```

MCP currently remains read-only:

```text
CLICKHOUSE_ALLOW_WRITE_ACCESS=false
```

State-changing application operations remain behind controlled tools and human approval.

---

# Known Limitations

Premiere currently does not:

- publish directly to real social-media platforms;
- automatically schedule campaign posts;
- use real production engagement data;
- automatically approve content;
- automatically execute optimisation recommendations;
- provide completed production Google Cloud deployment;
- measure the outcome of Content ID 14 yet;
- provide completed semantic/vector asset retrieval.

The current Campaign 3 engagement dataset is simulated.

---

# Known Grounding Improvements

Testing has exposed several useful failure modes.

### Film metadata inference

A film title must not be treated as evidence of setting, plot or filming location.

### Review rewrites

A Review Agent that correctly blocks an unsupported claim must not introduce another unsupported claim in its suggested rewrite.

### Optimisation experiments

Optimisation recommendations must not assume unavailable campaign resources.

For example:

```text
"Buy Tickets Now"
```

requires verified ticket availability and should not be proposed as established campaign functionality without that evidence.

These failures are treated as engineering evidence and are used to strengthen agent boundaries.

---

# Next Milestone

The next major closed-loop milestone is:

```text
Content ID 14
      ↓
Generate grounded TikTok experiment
      ↓
Review
      ↓
Human approval
      ↓
Simulated experiment results
      ↓
ClickHouse
      ↓
Analytics
      ↓
Compare against 1.60% baseline
      ↓
Determine whether Recommendation ID 1 worked
```

This will extend Premiere from:

```text
recommendation → experiment
```

to:

```text
recommendation
      ↓
experiment
      ↓
measured outcome
      ↓
learning
```

---

# Future ClickHouse Work

Planned ClickHouse-focused improvements include:

- experiment-result comparison;
- recommendation outcome tracking;
- richer recommendation lifecycle history;
- materialized operational agent-performance rollups;
- token-usage analytics;
- improved entity extraction from MCP SQL telemetry;
- vector embeddings for approved film assets;
- ClickHouse vector similarity search;
- hybrid semantic + metadata retrieval.

---

# Development Philosophy

Premiere is developed incrementally:

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
Independently Verify State
  ↓
Document
  ↓
Commit
```

A capability is not considered implemented merely because an agent produced a plausible answer.

Where important, the project verifies:

- exact database state;
- exact requested records;
- actual tool execution;
- actual agent delegation;
- ADK traces;
- ClickHouse persistence;
- absence of unintended mutations.

This discipline is particularly important in multi-agent systems, where a plausible natural-language result does not by itself prove that the intended architecture executed.

---

# Hackathon Position

Premiere currently demonstrates a multi-agent film campaign system in which:

```text
Gemini reasons
Google ADK orchestrates
ClickHouse remembers
ClickHouse analyses
MCP grounds agents
Humans govern consequential actions
Performance feeds future decisions
```

The goal is not simply to automate social-media copywriting.

The goal is to demonstrate an **AI studio producer that can plan, create, evaluate, learn and adapt while keeping humans in control of consequential campaign decisions.**
