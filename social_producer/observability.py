import time
import uuid

from social_producer.database import log_agent_event


_tool_start_times = {}


def _session_id(tool_context) -> str:
    """
    Try to reuse the ADK invocation/session identifier.

    Falls back to a generated local identifier if unavailable.
    """
    invocation_id = getattr(tool_context, "invocation_id", None)

    if invocation_id:
        return str(invocation_id)

    return f"local-{uuid.uuid4()}"


def before_tool_observer(tool, args, tool_context):
    """
    Runs immediately before an ADK tool executes.

    Records the start time so latency can be calculated later.
    """

    call_id = getattr(tool_context, "function_call_id", None)

    if call_id:
        _tool_start_times[call_id] = time.perf_counter()

    return None


def after_tool_observer(tool, args, tool_context, tool_response):
    """
    Runs after a tool successfully executes.

    Stores one observability event in ClickHouse.
    """

    call_id = getattr(tool_context, "function_call_id", None)

    start_time = _tool_start_times.pop(call_id, None)

    latency_ms = 0

    if start_time is not None:
        latency_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

    campaign_id = args.get("campaign_id")
    content_id = args.get("content_id")

    log_agent_event(
        session_id=_session_id(tool_context),
        parent_agent="",
        agent_name="social_media_producer",
        event_type="tool_call",
        tool_name=tool.name,
        campaign_id=campaign_id,
        content_id=content_id,
        status="success",
        error_code="",
        model_name="gemini-3.5-flash",
        grounding_result="not_applicable",
        latency_ms=latency_ms,
        input_tokens=0,
        output_tokens=0,
    )

    return None


def tool_error_observer(tool, args, tool_context, error):
    """
    Runs when an ADK tool execution raises an exception.

    Logs the failure but allows ADK's normal error handling to continue.
    """

    call_id = getattr(tool_context, "function_call_id", None)

    start_time = _tool_start_times.pop(call_id, None)

    latency_ms = 0

    if start_time is not None:
        latency_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

    campaign_id = args.get("campaign_id")
    content_id = args.get("content_id")

    log_agent_event(
        session_id=_session_id(tool_context),
        parent_agent="",
        agent_name="social_media_producer",
        event_type="tool_error",
        tool_name=tool.name,
        campaign_id=campaign_id,
        content_id=content_id,
        status="error",
        error_code=type(error).__name__,
        model_name="gemini-3.5-flash",
        grounding_result="not_applicable",
        latency_ms=latency_ms,
        input_tokens=0,
        output_tokens=0,
    )

    return None
