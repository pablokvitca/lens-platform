/**
 * Manages anonymous session token for progress tracking.
 *
 * The token is a UUID stored in localStorage, sent as X-Session-Token header.
 * On login, call claimSessionRecords() to associate anonymous progress with user.
 */

import { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";

const SESSION_TOKEN_KEY = "session_token";

export function useSessionToken() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // Get or create session token
    let stored = localStorage.getItem(SESSION_TOKEN_KEY);
    if (!stored) {
      stored = uuidv4();
      localStorage.setItem(SESSION_TOKEN_KEY, stored);
    }
    setToken(stored);
  }, []);

  const clearToken = useCallback(() => {
    localStorage.removeItem(SESSION_TOKEN_KEY);
    setToken(null);
  }, []);

  return { token, clearToken };
}

/**
 * Get session token synchronously (for use in API calls).
 */
export function getSessionToken(): string {
  let token = localStorage.getItem(SESSION_TOKEN_KEY);
  if (!token) {
    token = uuidv4();
    localStorage.setItem(SESSION_TOKEN_KEY, token);
  }
  return token;
}
