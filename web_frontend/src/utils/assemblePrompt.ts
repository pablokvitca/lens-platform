/**
 * Default base system prompt — matches the hardcoded prompt in core/modules/chat.py.
 */
export const DEFAULT_SYSTEM_PROMPT =
  "You are a tutor helping someone learn about AI safety. Each piece of content (article, video) has different topics and learning objectives.";

/**
 * Assemble a full system prompt from its three parts.
 * Mirrors _build_system_prompt() in core/modules/chat.py.
 */
export function assemblePrompt(
  systemPrompt: string,
  instructions: string,
  context: string,
): string {
  let prompt = systemPrompt;
  if (instructions) {
    prompt += "\n\nInstructions:\n" + instructions;
  }
  if (context) {
    prompt +=
      "\n\nThe user just engaged with this content:\n---\n" + context + "\n---";
  }
  return prompt;
}
