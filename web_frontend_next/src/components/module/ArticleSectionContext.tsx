// web_frontend_next/src/components/module/ArticleSectionContext.tsx
"use client";

import { createContext, useContext } from "react";

type ArticleSectionContextValue = {
  onHeadingRender: (id: string, element: HTMLElement) => void;
};

const ArticleSectionContext = createContext<ArticleSectionContextValue | null>(
  null
);

export function useArticleSectionContext() {
  return useContext(ArticleSectionContext);
}

export const ArticleSectionProvider = ArticleSectionContext.Provider;
