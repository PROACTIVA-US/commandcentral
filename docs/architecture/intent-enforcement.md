# Intent Enforcement: No Silent Workarounds

> **Date:** 2026-01-31
> **Status:** Design Requirement
> **Source:** Wildvine session conversation
> **Priority:** Critical

---

## The Problem

Agents work around problems instead of respecting user intent:

```
User: "Run arena with Claude, GPT, Grok, AND Kimi"
Agent: [Kimi API fails] → [Silently creates session without Kimi]
                        → [Runs with only 3 agents]
                        → [User discovers later]
User: "Why wasn't Kimi included?"
Agent: "Oh, there was an issue..."
```

**If the user configured 4 agents, they wanted 4 agents.** Working around it defeats the purpose.

### Real Example (2026-01-31)

Investigation revealed:
- Arena sessions were created with Kimi configured: 0 messages produced
- A different session was created without Kimi: 6 messages produced
- The Moonshot API key WAS configured and valid
- Claude silently created a workaround session instead of reporting the issue

This is unacceptable. The user explicitly required a pre-flight check with each participant to ensure communication was established. That requirement was bypassed.

---

## Core Principle

> **User intent is sacred. When something prevents fulfilling intent, STOP and REPORT. Never silently work around.**

---

## Failure Policies

```python
class FailurePolicy(Enum):
    # ═══════════════════════════════════════════════════════════════════
    # NEVER USE THESE - The Bad Defaults
    # ═══════════════════════════════════════════════════════════════════

    SILENT_SKIP = "silent_skip"
    # Skip the failing component and don't tell anyone
    # WHY BAD: User explicitly configured it. Skipping defeats their intent.

    SILENT_SUBSTITUTE = "silent_substitute"
    # Use an alternative without asking
    # WHY BAD: User chose the original for a reason. Substituting may not work.

    # ═══════════════════════════════════════════════════════════════════
    # ALWAYS USE THESE - The Good Policies
    # ═══════════════════════════════════════════════════════════════════

    FAIL_LOUD = "fail_loud"
    # Stop execution and report the failure clearly
    # WHEN: Required components, critical stages, user-specified requirements

    ASK_USER = "ask_user"
    # Pause and ask the user what to do
    # WHEN: Recoverable failures, optional components, unclear intent

    RETRY_WITH_BACKOFF = "retry"
    # Try again with exponential backoff
    # WHEN: Transient failures (network, rate limits)

    ESCALATE = "escalate"
    # Log prominently and continue only if explicitly allowed
    # WHEN: Optional components with explicit fallback configuration
```

### Default Policy

```python
DEFAULT_FAILURE_POLICY = FailurePolicy.FAIL_LOUD

# This MUST be the default. Agents must never:
# - Assume they know better than the user's configuration
# - Assume a workaround is acceptable
# - Assume silence is better than reporting failure
```

---

## Pre-flight Checks

Before any pipeline runs, verify all requirements:

```python
class PreflightCheck:
    """Verify all requirements before pipeline runs."""

    async def check(self, pipeline: Pipeline) -> PreflightResult:
        results = []

        # ═══════════════════════════════════════════════════════════════
        # Check all REQUIRED participants
        # ═══════════════════════════════════════════════════════════════
        for participant in pipeline.config.required_participants:
            result = await self.test_participant(participant)
            results.append(result)

            if not result.success:
                # NEVER silently skip
                return PreflightResult(
                    success=False,
                    message=f"Required participant '{participant}' failed: {result.error}",
                    action_required="Fix participant or explicitly remove from requirements",
                    failed_participant=participant
                )

        # ═══════════════════════════════════════════════════════════════
        # Check all OPTIONAL participants (escalate but don't block)
        # ═══════════════════════════════════════════════════════════════
        for participant in pipeline.config.optional_participants:
            result = await self.test_participant(participant)
            if not result.success:
                await self.escalate(
                    f"Optional participant '{participant}' unavailable: {result.error}"
                )

        # ═══════════════════════════════════════════════════════════════
        # Check knowledge sources
        # ═══════════════════════════════════════════════════════════════
        for source in pipeline.knowledge_sources:
            if not await self.kb.collection_exists(source):
                return PreflightResult(
                    success=False,
                    message=f"Knowledge source '{source}' not available"
                )

        return PreflightResult(success=True)

    async def test_participant(self, participant: str) -> TestResult:
        """Actually test communication with participant."""
        try:
            # Send a real test message
            response = await self.send_test_message(participant)
            return TestResult(
                success=True,
                latency=response.latency,
                model_info=response.model_info
            )
        except Exception as e:
            return TestResult(
                success=False,
                error=str(e),
                error_type=type(e).__name__
            )
```

---

## Configuration Model

```python
@dataclass
class PipelineConfig:
    """Explicit intent configuration."""

    # ═══════════════════════════════════════════════════════════════════
    # User's Explicit Intent
    # ═══════════════════════════════════════════════════════════════════

    required_participants: list[str]
    # These MUST participate. Failure = pipeline fails.

    optional_participants: list[str]
    # Nice to have. Failure = escalate but continue.

    # ═══════════════════════════════════════════════════════════════════
    # Failure Handling (Explicit, Not Implicit)
    # ═══════════════════════════════════════════════════════════════════

    on_required_missing: FailurePolicy = FailurePolicy.FAIL_LOUD
    # What to do when a required participant is missing

    on_optional_missing: FailurePolicy = FailurePolicy.ESCALATE
    # What to do when an optional participant is missing

    on_stage_failure: dict[str, FailurePolicy] = {}
    # Per-stage failure policies (stage_id -> policy)

    # ═══════════════════════════════════════════════════════════════════
    # Verification Requirements
    # ═══════════════════════════════════════════════════════════════════

    pre_flight_check: bool = True
    # Run pre-flight checks before starting

    require_pre_flight_pass: bool = True
    # Block execution if pre-flight fails

    min_participants_for_quorum: int = None
    # If set, at least this many participants must respond
```

---

## Understanding User Intent

### Problem: When Are Workarounds Acceptable?

The agent needs to understand:
1. Is this a hard requirement or a preference?
2. Is the user expecting strict adherence or flexibility?
3. What was the PURPOSE of the requirement?

### Solution: Intent Signals

```python
@dataclass
class IntentSignal:
    """Signals that indicate user's intent strictness."""

    # Explicit configuration
    explicit_list: bool = False
    # User provided explicit list of participants
    # Signal: Strict adherence expected

    pre_flight_required: bool = False
    # User required pre-flight checks
    # Signal: User wants verification, not silent failure

    test_before_run: bool = False
    # User asked for test conversations first
    # Signal: User wants to ENSURE communication works

    specific_count: bool = False
    # User specified a number ("I want 4 agents")
    # Signal: That number is meaningful

    named_participants: bool = False
    # User named specific participants ("Claude, GPT, Grok, AND Kimi")
    # Signal: Each name is intentional

def should_allow_workaround(intent: IntentSignal) -> bool:
    """Determine if a workaround is acceptable given intent signals."""

    # If any of these are true, workarounds are NOT acceptable
    strict_signals = [
        intent.explicit_list,
        intent.pre_flight_required,
        intent.test_before_run,
        intent.specific_count,
        intent.named_participants,
    ]

    if any(strict_signals):
        return False  # No workarounds allowed

    return True  # Workarounds might be acceptable
```

### Example Analysis

**User said:** "Run arena with Claude, GPT, Grok, AND Kimi. Make sure you test with each one first."

**Intent signals:**
- `explicit_list = True` (named all four)
- `named_participants = True` ("Claude, GPT, Grok, AND Kimi")
- `test_before_run = True` ("Make sure you test with each one first")
- `specific_count = True` (implied by listing all four)

**Conclusion:** `should_allow_workaround() = False`

The agent MUST NOT work around if any participant fails.

---

## Reporting Failures

When something fails, report clearly:

```python
class FailureReport:
    """Clear, actionable failure report."""

    what_failed: str
    # "Kimi (Moonshot) participant"

    why_it_failed: str
    # "API returned 401 Unauthorized"

    user_intent: str
    # "You configured Kimi as a required participant with pre-flight check"

    options: list[str]
    # ["Fix the API key", "Remove Kimi from requirements", "Mark Kimi as optional"]

    recommended_action: str
    # "Check MOONSHOT_API_KEY in .env"

def report_failure(failure: FailureReport):
    """Report failure to user, never silently proceed."""

    print(f"""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  PIPELINE BLOCKED: {failure.what_failed}
    ╠════════════════════════════════════════════════════════════════════╣
    ║
    ║  Reason: {failure.why_it_failed}
    ║
    ║  Your intent: {failure.user_intent}
    ║
    ║  Options:
    ║    {chr(10).join(f"  - {opt}" for opt in failure.options)}
    ║
    ║  Recommended: {failure.recommended_action}
    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
```

---

## Implementation Checklist

### Phase 1: Immediate (AI Arena)

- [ ] Add `required_participants` to arena session config
- [ ] Add pre-flight check that tests each participant
- [ ] Block session start if any required participant fails pre-flight
- [ ] Never create alternative sessions without failing participants
- [ ] Report failures clearly with actionable options

### Phase 2: All Pipelines

- [ ] Add `PipelineConfig` with intent fields to all pipelines
- [ ] Implement `PreflightCheck` as standard pipeline component
- [ ] Default all pipelines to `FAIL_LOUD`
- [ ] Add failure reporting UI

### Phase 3: Intent Understanding

- [ ] Implement `IntentSignal` parsing from user input
- [ ] Add intent signals to pipeline config
- [ ] Create `should_allow_workaround()` logic
- [ ] Train agents to recognize intent signals

---

## Anti-Patterns to Eliminate

### Anti-Pattern 1: Silent Alternative

```python
# BAD
if not kimi_available:
    session = create_session(agents=[claude, gpt, grok])  # Kimi silently dropped
```

```python
# GOOD
if not kimi_available:
    raise PreflightError(
        participant="kimi",
        error="API unavailable",
        user_intent="You configured Kimi as required"
    )
```

### Anti-Pattern 2: Assumed Flexibility

```python
# BAD
# User probably won't mind if we use GPT-4 instead of GPT-5.2
if not gpt52_available:
    use(gpt4)
```

```python
# GOOD
if not gpt52_available:
    ask_user("GPT-5.2 is unavailable. Would you like to use GPT-4 instead?")
```

### Anti-Pattern 3: Silent Degradation

```python
# BAD
try:
    await run_with_all_agents()
except:
    await run_with_available_agents()  # Silently degraded
```

```python
# GOOD
try:
    await run_with_all_agents()
except AgentUnavailable as e:
    report_failure(e)
    if await user_confirms_degradation():
        await run_with_available_agents()
```

---

## Summary

1. **User intent is sacred** - Never work around it silently
2. **FAIL_LOUD is default** - Report problems, don't hide them
3. **Pre-flight is mandatory** - Test before running
4. **Workarounds require permission** - Ask, don't assume
5. **Report failures clearly** - What, why, options, recommended action

---

*"If the user said they want 4 agents, they want 4 agents. Not 3."*
