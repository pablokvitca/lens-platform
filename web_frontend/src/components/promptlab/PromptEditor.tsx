interface PromptEditorProps {
  systemPrompt: string;
  onSystemPromptChange: (prompt: string) => void;
  onReset: () => void;
  isModified: boolean;
}

/**
 * Left panel of the Prompt Lab: monospace textarea for editing the system prompt.
 *
 * No submit button here -- regeneration is triggered from the conversation panel
 * via message selection. This is a scratchpad for iteration.
 */
export default function PromptEditor({
  systemPrompt,
  onSystemPromptChange,
  onReset,
  isModified,
}: PromptEditorProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-slate-700">
            System Prompt
          </h2>
          {isModified && (
            <span className="inline-block w-2 h-2 rounded-full bg-amber-400" title="Modified" />
          )}
        </div>
        <button
          onClick={onReset}
          disabled={!isModified}
          className={`text-xs px-2.5 py-1 rounded transition-colors ${
            isModified
              ? "text-slate-600 bg-slate-100 hover:bg-slate-200"
              : "text-slate-300 bg-slate-50 cursor-default"
          }`}
        >
          Reset to original
        </button>
      </div>

      {/* Textarea */}
      <textarea
        value={systemPrompt}
        onChange={(e) => onSystemPromptChange(e.target.value)}
        className="flex-1 w-full resize-none p-4 font-mono text-sm text-slate-800 leading-relaxed border-none outline-none focus:ring-0 bg-white"
        spellCheck={false}
      />
    </div>
  );
}
