"use client";

import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import Link from "next/link";
import Module from "@/views/Module";
import { getModule } from "@/api/modules";
import type { Module as ModuleType } from "@/types/module";

export default function ModulePage() {
  const params = useParams();
  const moduleId = (params?.moduleId as string) ?? "";

  const [moduleData, setModuleData] = useState<ModuleType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!moduleId) return;

    async function load() {
      try {
        const data = await getModule(moduleId);
        setModuleData(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load module");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [moduleId]);

  if (!moduleId || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading module...</p>
      </div>
    );
  }

  if (error || !moduleData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error ?? "Module not found"}</p>
          <Link href="/course" className="text-blue-600 hover:underline">
            Back to course
          </Link>
        </div>
      </div>
    );
  }

  return <Module module={moduleData} />;
}
