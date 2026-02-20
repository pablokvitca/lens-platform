"""
AI feedback module for post-answer conversations.

Builds feedback-specific system prompts from question context, student answer,
and mode (socratic vs assessment). Streams responses via LiteLLM for multi-turn
feedback conversations. Uses the same chat_sessions infrastructure as module chat.
"""

import logging
from typing import AsyncIterator

from core.modules.llm import stream_chat

logger = logging.getLogger(__name__)


def build_feedback_prompt(
    *,
    answer_text: str,
    user_instruction: str,
    assessment_prompt: str | None,
    learning_outcome_name: str | None,
    mode: str,
) -> str:
    """
    Build a system prompt for feedback conversation.

    This is a pure function that returns a system prompt string.
    Unlike the scoring prompt (which returns a tuple of system + messages),
    feedback only needs the system prompt -- messages come from the chat session.

    Args:
        answer_text: The student's response text
        user_instruction: The question text shown to the student
        assessment_prompt: Optional rubric/assessment criteria
        learning_outcome_name: Optional learning outcome name for context
        mode: "socratic" or "assessment"

    Returns:
        System prompt string for the feedback conversation
    """
    if mode == "socratic":
        system = (
            "You are a supportive tutor providing feedback on a student's response. "
            "Focus on what the student understood well, gently point out gaps, and "
            "ask Socratic questions to deepen their understanding. "
            "Be encouraging and constructive."
        )
    else:  # assessment
        system = (
            "You are an educational assessor providing feedback on a student's response. "
            "Evaluate the response against the rubric. Point out strengths and weaknesses "
            "with specific references to the student's answer. "
            "Suggest concrete improvements."
        )

    system += f"\n\nQuestion: {user_instruction}"

    if learning_outcome_name:
        system += f"\nLearning Outcome: {learning_outcome_name}"

    if assessment_prompt:
        system += f"\nRubric:\n{assessment_prompt}"

    system += f"\n\nStudent's answer:\n{answer_text}"

    return system


async def send_feedback_message(
    messages: list[dict],
    question_context: dict,
    answer_text: str,
    provider: str | None = None,
) -> AsyncIterator[dict]:
    """
    Stream a feedback response from the LLM.

    Builds the feedback system prompt from question context and answer,
    then delegates to stream_chat for actual LLM interaction.

    Args:
        messages: Conversation history (user + assistant messages)
        question_context: Dict from _resolve_question_details with keys:
            user_instruction, assessment_prompt, learning_outcome_name, mode
        answer_text: The student's answer text
        provider: Optional LLM provider override

    Yields:
        Normalized events: {"type": "text", "content": str}, {"type": "done"}
    """
    system = build_feedback_prompt(
        answer_text=answer_text,
        user_instruction=question_context.get("user_instruction", ""),
        assessment_prompt=question_context.get("assessment_prompt"),
        learning_outcome_name=question_context.get("learning_outcome_name"),
        mode=question_context.get("mode", "socratic"),
    )

    async for event in stream_chat(
        messages=messages,
        system=system,
        provider=provider,
        max_tokens=1024,
    ):
        yield event
