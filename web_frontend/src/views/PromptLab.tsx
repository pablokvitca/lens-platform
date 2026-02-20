import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import FixtureBrowser from "@/components/promptlab/FixtureBrowser";
import type { Fixture } from "@/api/promptlab";

/**
 * Prompt Lab view -- facilitator tool for testing system prompt variations.
 *
 * This is a placeholder that renders the FixtureBrowser as the initial view.
 * Plan 04 replaces the fixture-loaded state with the full two-panel layout
 * (system prompt editor + conversation panel).
 */
export default function PromptLab() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const [selectedFixture, setSelectedFixture] = useState<Fixture | null>(null);

  if (isLoading) {
    return (
      <div className="py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-stone-200 rounded" />
          <div className="h-4 w-64 bg-stone-200 rounded" />
          <div className="h-32 bg-stone-200 rounded" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="py-8">
        <h1 className="text-2xl font-bold mb-4">Prompt Lab</h1>
        <p className="mb-4 text-slate-600">
          Please sign in to access the Prompt Lab.
        </p>
        <button
          onClick={login}
          className="bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
        >
          Sign in with Discord
        </button>
      </div>
    );
  }

  if (selectedFixture) {
    return (
      <div className="py-4">
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={() => setSelectedFixture(null)}
            className="text-sm text-slate-500 hover:text-slate-700 transition-colors"
          >
            &larr; Back to fixtures
          </button>
          <h1 className="text-xl font-bold text-slate-900">
            {selectedFixture.name}
          </h1>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <p className="text-slate-600">
            Fixture loaded: <strong>{selectedFixture.name}</strong>
          </p>
          <p className="text-sm text-slate-400 mt-2">
            {selectedFixture.messages.length} messages from module{" "}
            &ldquo;{selectedFixture.module}&rdquo;
          </p>
          <p className="text-sm text-slate-400 mt-1">
            Full evaluation UI will be added in Plan 04.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-4">
      <div className="mb-4">
        <h1 className="text-xl font-bold text-slate-900">Prompt Lab</h1>
        <p className="text-sm text-slate-500 mt-1">
          Test system prompt variations against saved conversation fixtures.
        </p>
      </div>
      <FixtureBrowser onSelectFixture={setSelectedFixture} />
    </div>
  );
}
