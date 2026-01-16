"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { initPostHog, capturePageView, hasConsent } from "@/analytics";
import { initSentry } from "@/errorTracking";

export function Providers({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Initialize analytics if user previously consented
  useEffect(() => {
    if (hasConsent()) {
      initPostHog();
      initSentry();
    }
  }, []);

  // Track page views on route change
  useEffect(() => {
    capturePageView(pathname);
  }, [pathname]);

  return <>{children}</>;
}
