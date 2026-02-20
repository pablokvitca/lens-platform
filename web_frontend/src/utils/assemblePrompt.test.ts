import { describe, it, expect } from "vitest";
import { assemblePrompt, DEFAULT_SYSTEM_PROMPT } from "./assemblePrompt";

describe("assemblePrompt", () => {
  it("returns just system prompt when no instructions or context", () => {
    expect(assemblePrompt("Base prompt", "", "")).toBe("Base prompt");
  });

  it("appends instructions", () => {
    const result = assemblePrompt("Base", "Do this thing", "");
    expect(result).toBe("Base\n\nInstructions:\nDo this thing");
  });

  it("appends context", () => {
    const result = assemblePrompt("Base", "", "Some content");
    expect(result).toBe(
      "Base\n\nThe user just engaged with this content:\n---\nSome content\n---"
    );
  });

  it("appends both instructions and context", () => {
    const result = assemblePrompt("Base", "Do this", "Content here");
    expect(result).toContain("Instructions:\nDo this");
    expect(result).toContain("---\nContent here\n---");
    expect(result.indexOf("Instructions")).toBeLessThan(
      result.indexOf("Content here")
    );
  });

  it("exports a DEFAULT_SYSTEM_PROMPT constant", () => {
    expect(DEFAULT_SYSTEM_PROMPT).toContain("tutor");
    expect(DEFAULT_SYSTEM_PROMPT).toContain("AI safety");
  });
});
