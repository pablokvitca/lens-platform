# LiteLLM Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace direct Anthropic SDK usage with LiteLLM to enable runtime switching between Claude and Gemini (and other providers) for the AI Tutor.

**Architecture:** Create a thin wrapper module `core/lessons/llm.py` that uses LiteLLM for all AI provider calls. The wrapper normalizes streaming events to our existing format, allowing `chat.py` to remain largely unchanged. Provider selection happens at runtime via a `provider` parameter, enabling A/B testing and provider fallback.

**Tech Stack:** LiteLLM, Python 3.11+, async/await

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Update dependencies | `requirements.txt` |
| 2 | Create LLM wrapper module | `core/lessons/llm.py` (new) |
| 3 | Write tests for LLM wrapper | `core/lessons/tests/test_llm.py` (new) |
| 4 | Update chat.py to use wrapper | `core/lessons/chat.py` |
| 5 | Update exports | `core/lessons/__init__.py` |
| 6 | Update environment config | `.env.example` |
| 7 | Integration test | Manual verification |

---

## Task 1: Update Dependencies

**Files:**
- Modify: `requirements.txt:15`

**Step 1: Replace anthropic with litellm**

Find this line:
```
anthropic>=0.40.0
```

Replace with:
```
litellm>=1.40.0
```

Note: LiteLLM installs `anthropic` and `google-generativeai` as sub-dependencies when those providers are used.

**Step 2: Install new dependencies**

Run:
```bash
pip install -r requirements.txt
```

Expected: LiteLLM and its dependencies install successfully.

**Step 3: Commit**

```bash
jj describe -m "chore: replace anthropic SDK with litellm for multi-provider support"
```

---

## Task 2: Create LLM Wrapper Module

**Files:**
- Create: `core/lessons/llm.py`

**Step 1: Create the wrapper module**

```python
"""
LLM provider abstraction using LiteLLM.

Provides a unified interface for Claude, Gemini, and other providers.
Normalizes streaming events to our internal format.
"""

import os
from typing import AsyncIterator

from litellm import acompletion


# Default provider - can be overridden per-call or via environment
DEFAULT_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic/claude-sonnet-4-20250514")


async def stream_chat(
    messages: list[dict],
    system: str,
    tools: list[dict] | None = None,
    provider: str | None = None,
    max_tokens: int = 1024,
) -> AsyncIterator[dict]:
    """
    Stream a chat completion from any LLM provider.

    Args:
        messages: List of {"role": "user"|"assistant", "content": str}
        system: System prompt
        tools: Optional list of tool definitions (OpenAI format)
        provider: Model string like "anthropic/claude-sonnet-4-20250514" or "gemini/gemini-1.5-pro"
        max_tokens: Maximum tokens in response

    Yields:
        Normalized events:
        - {"type": "text", "content": str} for text chunks
        - {"type": "tool_use", "name": str} for tool calls
        - {"type": "done"} when complete
    """
    model = provider or DEFAULT_PROVIDER

    # LiteLLM uses OpenAI-style messages with system as a message
    llm_messages = [{"role": "system", "content": system}] + messages

    # Build kwargs
    kwargs = {
        "model": model,
        "messages": llm_messages,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = tools

    response = await acompletion(**kwargs)

    # Track if we're in a tool call
    current_tool_name = None

    async for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if not delta:
            continue

        # Handle text content
        if delta.content:
            yield {"type": "text", "content": delta.content}

        # Handle tool calls
        if delta.tool_calls:
            for tool_call in delta.tool_calls:
                if tool_call.function and tool_call.function.name:
                    # New tool call starting
                    current_tool_name = tool_call.function.name
                    yield {"type": "tool_use", "name": current_tool_name}

    yield {"type": "done"}
```

**Step 2: Verify file was created**

Run:
```bash
ls -la core/lessons/llm.py
```

Expected: File exists with correct permissions.

**Step 3: Commit**

```bash
jj describe -m "feat: add LLM wrapper module using LiteLLM"
```

---

## Task 3: Write Tests for LLM Wrapper

**Files:**
- Create: `core/lessons/tests/test_llm.py`

**Step 1: Create test file with mock tests**

```python
"""Tests for LLM wrapper module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_stream_chat_yields_text_chunks():
    """Should yield text chunks from streaming response."""
    from core.lessons.llm import stream_chat

    # Create mock chunk with text content
    mock_delta = MagicMock()
    mock_delta.content = "Hello"
    mock_delta.tool_calls = None

    mock_choice = MagicMock()
    mock_choice.delta = mock_delta

    mock_chunk = MagicMock()
    mock_chunk.choices = [mock_choice]

    # Create async iterator from mock chunks
    async def mock_response():
        yield mock_chunk

    with patch("core.lessons.llm.acompletion", return_value=mock_response()):
        events = []
        async for event in stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system="You are helpful.",
            provider="anthropic/claude-sonnet-4-20250514",
        ):
            events.append(event)

        assert {"type": "text", "content": "Hello"} in events
        assert {"type": "done"} in events


@pytest.mark.asyncio
async def test_stream_chat_yields_tool_calls():
    """Should yield tool_use events when model calls a tool."""
    from core.lessons.llm import stream_chat

    # Create mock chunk with tool call
    mock_tool_call = MagicMock()
    mock_tool_call.function = MagicMock()
    mock_tool_call.function.name = "transition_to_next"

    mock_delta = MagicMock()
    mock_delta.content = None
    mock_delta.tool_calls = [mock_tool_call]

    mock_choice = MagicMock()
    mock_choice.delta = mock_delta

    mock_chunk = MagicMock()
    mock_chunk.choices = [mock_choice]

    async def mock_response():
        yield mock_chunk

    with patch("core.lessons.llm.acompletion", return_value=mock_response()):
        events = []
        async for event in stream_chat(
            messages=[{"role": "user", "content": "I'm ready"}],
            system="You are a tutor.",
            tools=[{"type": "function", "function": {"name": "transition_to_next"}}],
            provider="anthropic/claude-sonnet-4-20250514",
        ):
            events.append(event)

        assert {"type": "tool_use", "name": "transition_to_next"} in events


@pytest.mark.asyncio
async def test_stream_chat_uses_default_provider():
    """Should use DEFAULT_PROVIDER when no provider specified."""
    from core.lessons.llm import stream_chat, DEFAULT_PROVIDER

    async def mock_response():
        # Empty response
        return
        yield  # Make it a generator

    with patch("core.lessons.llm.acompletion", new_callable=AsyncMock) as mock_completion:
        # Make acompletion return an async generator
        async def empty_gen():
            return
            yield

        mock_completion.return_value = empty_gen()

        events = []
        async for event in stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system="Test",
        ):
            events.append(event)

        # Verify acompletion was called with default provider
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args[1]
        assert call_kwargs["model"] == DEFAULT_PROVIDER


@pytest.mark.asyncio
async def test_stream_chat_passes_tools_to_provider():
    """Should pass tools to LiteLLM when provided."""
    from core.lessons.llm import stream_chat

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]

    with patch("core.lessons.llm.acompletion", new_callable=AsyncMock) as mock_completion:
        async def empty_gen():
            return
            yield

        mock_completion.return_value = empty_gen()

        events = []
        async for event in stream_chat(
            messages=[{"role": "user", "content": "Weather?"}],
            system="Test",
            tools=tools,
            provider="gemini/gemini-1.5-pro",
        ):
            events.append(event)

        call_kwargs = mock_completion.call_args[1]
        assert call_kwargs["tools"] == tools
        assert call_kwargs["model"] == "gemini/gemini-1.5-pro"
```

**Step 2: Run the tests**

Run:
```bash
pytest core/lessons/tests/test_llm.py -v
```

Expected: All tests pass.

**Step 3: Commit**

```bash
jj describe -m "test: add unit tests for LLM wrapper module"
```

---

## Task 4: Update chat.py to Use Wrapper

**Files:**
- Modify: `core/lessons/chat.py`

**Step 1: Update imports**

Replace line 9:
```python
from anthropic import AsyncAnthropic
```

With:
```python
from .llm import stream_chat
```

**Step 2: Update TRANSITION_TOOL to OpenAI format**

Replace lines 24-36:
```python
# Tool for transitioning to next stage
TRANSITION_TOOL = {
    "name": "transition_to_next",
    "description": (
        "Call this when the conversation has reached a good stopping point "
        "and the user is ready to move to the next stage. "
        "Use this after 2-4 meaningful exchanges, or when the user indicates readiness."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}
```

With:
```python
# Tool for transitioning to next stage (OpenAI function calling format)
TRANSITION_TOOL = {
    "type": "function",
    "function": {
        "name": "transition_to_next",
        "description": (
            "Call this when the conversation has reached a good stopping point "
            "and the user is ready to move to the next stage. "
            "Use this after 2-4 meaningful exchanges, or when the user indicates readiness."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}
```

**Step 3: Update send_message function**

Replace the entire send_message function (lines 146-200) with:

```python
async def send_message(
    messages: list[dict],
    current_stage: Stage,
    current_content: str | None = None,
    previous_content: str | None = None,
    provider: str | None = None,
) -> AsyncIterator[dict]:
    """
    Send messages to an LLM and stream the response.

    Args:
        messages: List of {"role": "user"|"assistant"|"system", "content": str}
        current_stage: The current lesson stage
        current_content: Content of current stage (for article/video stages)
        previous_content: Content from previous stage (for chat stages)
        provider: LLM provider string (e.g., "anthropic/claude-sonnet-4-20250514")
                  If None, uses DEFAULT_PROVIDER from environment.

    Yields:
        Dicts with either:
        - {"type": "text", "content": str} for text chunks
        - {"type": "tool_use", "name": str} for tool calls
        - {"type": "done"} when complete
    """
    system = _build_system_prompt(current_stage, current_content, previous_content)

    # Debug mode: show system prompt in chat
    if os.environ.get("DEBUG") == "1":
        debug_text = f"**[DEBUG - System Prompt]**\n\n```\n{system}\n```\n\n**[DEBUG - Messages]**\n\n```\n{messages}\n```\n\n---\n\n"
        yield {"type": "text", "content": debug_text}

    # Filter out system messages (stage transition markers) - LLM APIs don't accept them in messages
    api_messages = [m for m in messages if m["role"] != "system"]

    # Only include transition tool for chat stages
    tools = [TRANSITION_TOOL] if isinstance(current_stage, ChatStage) else None

    async for event in stream_chat(
        messages=api_messages,
        system=system,
        tools=tools,
        provider=provider,
        max_tokens=1024,
    ):
        yield event
```

**Step 4: Verify changes compile**

Run:
```bash
python -c "from core.lessons.chat import send_message; print('OK')"
```

Expected: Prints "OK" with no errors.

**Step 5: Commit**

```bash
jj describe -m "refactor: update chat.py to use LiteLLM wrapper"
```

---

## Task 5: Update Exports

**Files:**
- Modify: `core/lessons/__init__.py`

**Step 1: Read current exports**

First check what's currently exported (no changes may be needed if send_message is already exported).

**Step 2: Add DEFAULT_PROVIDER export if needed**

If you want to expose the default provider for inspection/configuration, add to exports:

```python
from .llm import DEFAULT_PROVIDER
```

**Step 3: Commit if changes were made**

```bash
jj describe -m "chore: export DEFAULT_PROVIDER from lessons module"
```

---

## Task 6: Update Environment Config

**Files:**
- Modify: `.env.example`

**Step 1: Add LLM provider configuration**

Add these lines to `.env.example`:

```bash
# LLM Provider Configuration
# Default: anthropic/claude-sonnet-4-20250514
# Options: anthropic/claude-sonnet-4-20250514, gemini/gemini-1.5-pro, etc.
# LLM_PROVIDER=anthropic/claude-sonnet-4-20250514

# API Keys (set the ones you need)
ANTHROPIC_API_KEY=your-anthropic-key
# GEMINI_API_KEY=your-gemini-key
```

**Step 2: Update local .env.local**

Add your actual API keys to `.env.local` (gitignored).

**Step 3: Commit**

```bash
jj describe -m "docs: add LLM provider configuration to .env.example"
```

---

## Task 7: Integration Test

**Step 1: Start the dev server**

```bash
python main.py --dev
```

**Step 2: Test with Claude (default)**

1. Open a lesson in the browser
2. Send a chat message
3. Verify streaming response works
4. Verify tool calls work (transition_to_next)

**Step 3: Test with Gemini**

Set in `.env.local`:
```bash
LLM_PROVIDER=gemini/gemini-1.5-pro
GEMINI_API_KEY=your-key
```

Restart server and repeat Step 2.

**Step 4: Test runtime switching (optional)**

Modify the route handler temporarily to pass different providers per-request for A/B testing verification.

**Step 5: Final commit**

```bash
jj describe -m "feat: complete LiteLLM migration for multi-provider AI Tutor"
```

---

## Rollback Plan

If issues arise:

1. Revert requirements.txt to use `anthropic>=0.40.0`
2. Revert chat.py changes (restore AsyncAnthropic usage)
3. Delete `core/lessons/llm.py`
4. Run `pip install -r requirements.txt`

---

## Future Enhancements

After this migration is stable:

1. **A/B Testing**: Add provider selection logic based on user ID hash
2. **Fallback**: Use LiteLLM's fallback_models for resilience
3. **Cost Tracking**: Enable LiteLLM's cost tracking callbacks
4. **Prompt Caching**: Add cache_control support for Anthropic (already supported by LiteLLM)
5. **Observability**: Integrate LiteLLM with Langfuse or similar for monitoring
