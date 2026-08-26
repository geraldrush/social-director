"use client";

import { useEffect, useState } from "react";

type Campaign = {
  campaign_id: number;
  brand_name: string;
  objective: string;
  target_audience: string;
  platforms: string[];
  duration_days: number;
  status: string;
  created_at: string;
};

type PlatformPerformance = {
  platform: string;
  impressions: number;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number;
  clicks: number;
  engagement_rate: number;
  click_rate: number;
};

type Recommendation = {
  recommendation_id: number;
  campaign_id: number;
  recommendation_type: string;
  observation: string;
  hypothesis: string;
  recommendation: string;
  experiment: string;
  experiment_content_id: number | null;
  success_metric: string;
  status: string;
  created_at: string;
};

type AnalysisStep = {
  label: string;
  detail: string;
  status: "waiting" | "working" | "done";
};

export default function Home() {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [platforms, setPlatforms] = useState<PlatformPerformance[]>([]);
  const [recommendation, setRecommendation] =
    useState<Recommendation | null>(null);

  const [activeTab, setActiveTab] = useState("overview");
  const [analysing, setAnalysing] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  const [steps, setSteps] = useState<AnalysisStep[]>([
    {
      label: "Analytics Agent",
      detail: "Waiting to inspect ClickHouse campaign performance",
      status: "waiting",
    },
    {
      label: "Platform Analysis",
      detail: "Waiting for campaign metrics",
      status: "waiting",
    },
    {
      label: "Optimisation Agent",
      detail: "Waiting for analytical findings",
      status: "waiting",
    },
  ]);

  useEffect(() => {
    async function loadData() {
      try {
        setLoadingError(null);

        const [
          campaignResponse,
          platformResponse,
          recommendationResponse,
        ] = await Promise.all([
          fetch("http://localhost:8001/campaigns/3"),
          fetch("http://localhost:8001/campaigns/3/platforms"),
          fetch("http://localhost:8001/recommendations/1"),
        ]);

        if (!campaignResponse.ok) {
          throw new Error("Failed to load campaign data.");
        }

        if (!platformResponse.ok) {
          throw new Error("Failed to load platform performance.");
        }

        if (!recommendationResponse.ok) {
          throw new Error("Failed to load optimisation recommendation.");
        }

        const campaignData = await campaignResponse.json();
        const platformData = await platformResponse.json();
        const recommendationData = await recommendationResponse.json();

        setCampaign(campaignData);
        setPlatforms(platformData);
        setRecommendation(recommendationData);
      } catch (error) {
        console.error(error);

        setLoadingError(
          error instanceof Error
            ? error.message
            : "Unable to load Premiere data."
        );
      }
    }

    loadData();
  }, []);

  async function analyseCampaign() {
    if (analysing) return;

    setAnalysing(true);
    setAnalysisComplete(false);

    setSteps([
      {
        label: "Analytics Agent",
        detail: "Reading campaign performance from ClickHouse",
        status: "working",
      },
      {
        label: "Platform Analysis",
        detail: "Waiting for campaign metrics",
        status: "waiting",
      },
      {
        label: "Optimisation Agent",
        detail: "Waiting for analytical findings",
        status: "waiting",
      },
    ]);

    await new Promise((resolve) => setTimeout(resolve, 900));

    setSteps([
      {
        label: "Analytics Agent",
        detail: "Campaign performance retrieved",
        status: "done",
      },
      {
        label: "Platform Analysis",
        detail: "Comparing reach, engagement and click-through performance",
        status: "working",
      },
      {
        label: "Optimisation Agent",
        detail: "Waiting for analytical findings",
        status: "waiting",
      },
    ]);

    await new Promise((resolve) => setTimeout(resolve, 900));

    setSteps([
      {
        label: "Analytics Agent",
        detail: "Campaign performance retrieved",
        status: "done",
      },
      {
        label: "Platform Analysis",
        detail: "TikTok shows strong engagement but weaker click efficiency",
        status: "done",
      },
      {
        label: "Optimisation Agent",
        detail: "Loading evidence-backed recommendation",
        status: "working",
      },
    ]);

    await new Promise((resolve) => setTimeout(resolve, 900));

    setSteps([
      {
        label: "Analytics Agent",
        detail: "Campaign performance retrieved",
        status: "done",
      },
      {
        label: "Platform Analysis",
        detail: "TikTok shows strong engagement but weaker click efficiency",
        status: "done",
      },
      {
        label: "Optimisation Agent",
        detail: recommendation
          ? `Recommendation #${recommendation.recommendation_id} retrieved`
          : "Recommendation retrieved",
        status: "done",
      },
    ]);

    setAnalysing(false);
    setAnalysisComplete(true);
  }

  if (loadingError) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-neutral-950 px-6 text-white">
        <div className="max-w-lg rounded-3xl border border-red-500/20 bg-red-500/[0.06] p-8 text-center">
          <p className="text-sm uppercase tracking-[0.2em] text-red-300">
            Premiere API Error
          </p>

          <h1 className="mt-3 text-2xl font-semibold">
            Unable to load campaign data
          </h1>

          <p className="mt-3 text-sm leading-6 text-neutral-400">
            {loadingError}
          </p>

          <p className="mt-5 text-xs text-neutral-600">
            Confirm that the FastAPI service is running on localhost:8001.
          </p>
        </div>
      </main>
    );
  }

  if (!campaign) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-neutral-950 text-white">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-white/20 border-t-white" />

          <p className="mt-4 text-sm text-neutral-500">
            Loading Premiere...
          </p>
        </div>
      </main>
    );
  }

  const tabs = [
    "overview",
    "insights",
    "content",
    "experiments",
    "activity",
  ];

  return (
    <main className="min-h-screen bg-neutral-950 text-white">
      <div className="mx-auto max-w-7xl px-6 py-6">
        <header className="flex flex-col gap-6 border-b border-white/10 pb-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.28em] text-neutral-500">
              AI Studio Producer
            </p>

            <h1 className="mt-2 text-3xl font-semibold tracking-tight">
              Premiere
            </h1>

            <p className="mt-2 text-sm text-neutral-500">
              Gemini · Google ADK · ClickHouse · MCP
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-neutral-400">
              {campaign.brand_name}
            </div>

            <div className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-300">
              Campaign {campaign.campaign_id} Active
            </div>
          </div>
        </header>

        <nav className="mt-6 flex gap-2 overflow-x-auto pb-1">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`rounded-full px-4 py-2 text-sm capitalize transition ${
                activeTab === tab
                  ? "bg-white text-black"
                  : "bg-white/[0.04] text-neutral-400 hover:bg-white/[0.08]"
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>

        {activeTab === "overview" && (
          <div className="mt-8">
            <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-7">
              <div className="flex flex-col justify-between gap-8 lg:flex-row">
                <div>
                  <p className="text-sm text-neutral-500">
                    Campaign {campaign.campaign_id}
                  </p>

                  <h2 className="mt-1 text-3xl font-semibold">
                    Shadows of Pretoria
                  </h2>

                  <p className="mt-2 text-neutral-400">
                    {campaign.brand_name}
                  </p>

                  <p className="mt-5 max-w-3xl leading-7 text-neutral-400">
                    {campaign.objective}
                  </p>
                </div>

                <div className="grid min-w-72 grid-cols-2 gap-6 text-sm">
                  <div>
                    <p className="text-neutral-500">Audience</p>
                    <p className="mt-1 leading-5 text-neutral-300">
                      {campaign.target_audience}
                    </p>
                  </div>

                  <div>
                    <p className="text-neutral-500">Duration</p>
                    <p className="mt-1 font-medium">
                      {campaign.duration_days} days
                    </p>
                  </div>

                  <div>
                    <p className="text-neutral-500">Status</p>
                    <p className="mt-1 capitalize">{campaign.status}</p>
                  </div>

                  <div>
                    <p className="text-neutral-500">Platforms</p>
                    <p className="mt-1">
                      {campaign.platforms.length}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section className="mt-8">
              <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
                <div>
                  <h2 className="text-xl font-semibold">
                    Current Platform Performance
                  </h2>

                  <p className="mt-1 text-sm text-neutral-500">
                    Live data from ClickHouse via the Premiere API
                  </p>
                </div>

                <span className="text-xs text-neutral-600">
                  Includes simulated development telemetry
                </span>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {platforms.map((platform) => (
                  <div
                    key={platform.platform}
                    className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 transition hover:border-white/20"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="font-medium">
                        {platform.platform}
                      </h3>

                      <span className="rounded-full bg-white/[0.05] px-2 py-1 text-[10px] uppercase tracking-wide text-neutral-500">
                        Live
                      </span>
                    </div>

                    <p className="mt-1 text-xs text-neutral-500">
                      {platform.impressions.toLocaleString()} impressions
                    </p>

                    <div className="mt-6 grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-wide text-neutral-500">
                          Engagement
                        </p>

                        <p className="mt-1 text-2xl font-semibold">
                          {platform.engagement_rate.toFixed(2)}%
                        </p>
                      </div>

                      <div>
                        <p className="text-xs uppercase tracking-wide text-neutral-500">
                          CTR
                        </p>

                        <p className="mt-1 text-2xl font-semibold">
                          {platform.click_rate.toFixed(2)}%
                        </p>
                      </div>
                    </div>

                    <div className="mt-5 border-t border-white/10 pt-4 text-xs text-neutral-500">
                      {platform.clicks.toLocaleString()} clicks ·{" "}
                      {platform.views.toLocaleString()} views
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {recommendation && (
              <section className="mt-8 rounded-3xl border border-amber-400/15 bg-amber-400/[0.04] p-7">
                <div className="flex flex-col justify-between gap-5 md:flex-row md:items-center">
                  <div>
                    <p className="text-sm text-amber-300">
                      Optimisation Recommendation #
                      {recommendation.recommendation_id}
                    </p>

                    <h2 className="mt-2 text-xl font-semibold">
                      TikTok click-through opportunity detected
                    </h2>

                    <p className="mt-2 max-w-3xl text-sm leading-6 text-neutral-400">
                      {recommendation.observation}
                    </p>
                  </div>

                  <button
                    onClick={() => {
                      setActiveTab("insights");
                      setAnalysisComplete(true);
                    }}
                    className="shrink-0 rounded-xl bg-white px-5 py-3 text-sm font-medium text-black transition hover:bg-neutral-200"
                  >
                    View Insight
                  </button>
                </div>
              </section>
            )}
          </div>
        )}

        {activeTab === "insights" && (
          <section className="mt-8 grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-7">
              <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
                <div>
                  <p className="text-sm text-neutral-500">
                    Campaign Intelligence
                  </p>

                  <h2 className="mt-1 text-2xl font-semibold">
                    Analyse Campaign {campaign.campaign_id}
                  </h2>

                  <p className="mt-2 text-sm text-neutral-500">
                    Agent workflow visualisation
                  </p>
                </div>

                <button
                  onClick={analyseCampaign}
                  disabled={analysing}
                  className="rounded-xl bg-white px-5 py-3 text-sm font-medium text-black transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {analysing
                    ? "Analysing..."
                    : analysisComplete
                    ? "Run Again"
                    : "Analyse Campaign"}
                </button>
              </div>

              <div className="mt-8 space-y-4">
                {steps.map((step, index) => (
                  <div
                    key={step.label}
                    className="rounded-2xl border border-white/10 bg-black/20 p-5"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex flex-col items-center">
                        <span
                          className={`mt-1 h-2.5 w-2.5 rounded-full ${
                            step.status === "done"
                              ? "bg-emerald-400"
                              : step.status === "working"
                              ? "animate-pulse bg-amber-300"
                              : "bg-neutral-700"
                          }`}
                        />

                        {index < steps.length - 1 && (
                          <span className="mt-2 h-8 w-px bg-white/10" />
                        )}
                      </div>

                      <div>
                        <div className="flex items-center gap-3">
                          <p className="font-medium">{step.label}</p>

                          <span
                            className={`text-[10px] uppercase tracking-wide ${
                              step.status === "done"
                                ? "text-emerald-400"
                                : step.status === "working"
                                ? "text-amber-300"
                                : "text-neutral-600"
                            }`}
                          >
                            {step.status}
                          </span>
                        </div>

                        <p className="mt-1 text-sm leading-6 text-neutral-500">
                          {step.detail}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 p-5">
                <p className="text-xs uppercase tracking-[0.18em] text-neutral-600">
                  Data path
                </p>

                <p className="mt-3 text-sm leading-6 text-neutral-400">
                  Premiere UI → FastAPI → database.py → ClickHouse
                </p>

                <p className="mt-1 text-xs text-neutral-600">
                  Agent-driven ClickHouse reads also use the official MCP
                  integration in the ADK runtime.
                </p>
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-7">
              <p className="text-sm text-neutral-500">
                AI Recommendation
              </p>

              {!analysisComplete ? (
                <div className="mt-8 flex min-h-80 items-center justify-center rounded-2xl border border-dashed border-white/10 px-6 text-center">
                  <div>
                    <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-white/[0.05] text-neutral-600">
                      AI
                    </div>

                    <p className="mt-4 text-sm text-neutral-600">
                      Run campaign analysis to reveal the persisted
                      optimisation insight.
                    </p>
                  </div>
                </div>
              ) : recommendation ? (
                <div className="mt-6">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300">
                      Recommendation #{recommendation.recommendation_id}
                    </span>

                    <span className="rounded-full bg-white/[0.06] px-3 py-1 text-xs uppercase tracking-wide text-neutral-400">
                      {recommendation.status.replaceAll("_", " ")}
                    </span>
                  </div>

                  <h3 className="mt-5 text-xl font-semibold">
                    Improve TikTok click-through performance
                  </h3>

                  <div className="mt-6 space-y-5 text-sm">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-neutral-500">
                        Observation
                      </p>

                      <p className="mt-2 leading-6 text-neutral-300">
                        {recommendation.observation}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs uppercase tracking-wide text-neutral-500">
                        Hypothesis
                      </p>

                      <p className="mt-2 leading-6 text-neutral-300">
                        {recommendation.hypothesis}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs uppercase tracking-wide text-neutral-500">
                        Recommendation
                      </p>

                      <p className="mt-2 leading-6 text-neutral-300">
                        {recommendation.recommendation}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs uppercase tracking-wide text-neutral-500">
                        Experiment
                      </p>

                      <p className="mt-2 leading-6 text-neutral-300">
                        {recommendation.experiment}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs uppercase tracking-wide text-neutral-500">
                        Success Metric
                      </p>

                      <p className="mt-2 leading-6 text-neutral-300">
                        {recommendation.success_metric}
                      </p>
                    </div>
                  </div>

                  {recommendation.experiment_content_id && (
                    <div className="mt-7 rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.05] p-5">
                      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                        <div>
                          <p className="text-xs uppercase tracking-wide text-emerald-300">
                            Applied to plan
                          </p>

                          <p className="mt-2 font-medium">
                            Experiment Content ID{" "}
                            {recommendation.experiment_content_id}
                          </p>

                          <p className="mt-1 text-xs text-neutral-500">
                            This recommendation has already passed the human
                            approval boundary and produced an experiment.
                          </p>
                        </div>

                        <button
                          onClick={() => setActiveTab("experiments")}
                          className="shrink-0 rounded-xl border border-white/10 px-4 py-3 text-sm text-neutral-300 transition hover:bg-white/[0.05]"
                        >
                          View Experiment
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="mt-8 rounded-2xl border border-red-500/20 bg-red-500/[0.05] p-5 text-sm text-red-200">
                  Recommendation data is unavailable.
                </div>
              )}
            </div>
          </section>
        )}

        {activeTab === "content" && (
          <section className="mt-8 rounded-3xl border border-white/10 bg-white/[0.04] p-10 text-center">
            <p className="text-sm text-neutral-500">
              Content Pipeline
            </p>

            <h2 className="mt-2 text-2xl font-semibold">
              Campaign Content
            </h2>

            <p className="mx-auto mt-3 max-w-xl text-neutral-500">
              Planned, generated and reviewed campaign content will be
              connected here next.
            </p>
          </section>
        )}

        {activeTab === "experiments" && (
          <section className="mt-8">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8">
              <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
                <div>
                  <p className="text-sm text-neutral-500">
                    Optimisation Experiments
                  </p>

                  <h2 className="mt-2 text-2xl font-semibold">
                    Experiment Result
                  </h2>

                  <p className="mt-3 max-w-2xl text-sm leading-6 text-neutral-500">
                    The next UI milestone will connect Experiment Result #1
                    directly from ClickHouse and display baseline versus
                    measured performance.
                  </p>
                </div>

                {recommendation?.experiment_content_id && (
                  <div className="rounded-full border border-white/10 bg-black/20 px-4 py-2 text-sm text-neutral-400">
                    Content ID {recommendation.experiment_content_id}
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {activeTab === "activity" && (
          <section className="mt-8 rounded-3xl border border-white/10 bg-white/[0.04] p-10 text-center">
            <p className="text-sm text-neutral-500">
              Agent Observability
            </p>

            <h2 className="mt-2 text-2xl font-semibold">
              Live Agent Activity
            </h2>

            <p className="mx-auto mt-3 max-w-xl text-neutral-500">
              Agent events, MCP calls, tool execution and latency from
              ClickHouse will appear here.
            </p>
          </section>
        )}

        <footer className="mt-10 flex flex-col gap-3 border-t border-white/10 py-6 text-xs text-neutral-600 sm:flex-row sm:items-center sm:justify-between">
          <span>Premiere — AI Studio Producer</span>

          <span>Gemini · Google ADK · ClickHouse · MCP</span>
        </footer>
      </div>
    </main>
  );
}