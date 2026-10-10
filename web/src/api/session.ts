/**
 * Refresh-token flow used by the fetch middleware. Independent of openapi-fetch so it can call the
 * api with a bare fetch and never recurses into the middleware itself.
 */
import { z } from 'zod';

import { clearSession, getTokens, setTokens, tokensFromApi, type StoredTokens } from '@/auth/atoms';

import { apiErrorFromResponse } from './api-error';

const tokenSetSchema = z.object({
  tokens: z.object({
    accessToken: z.string(),
    accessExpiresAt: z.string(),
    refreshToken: z.string(),
    refreshExpiresAt: z.string(),
  }),
});

let inFlight: Promise<StoredTokens | null> | null = null;

/**
 * Exchanges the stored refresh token for a new token set. Concurrent callers share one request.
 * Returns null (and clears the session) when the refresh token is missing, expired or rejected.
 */
export function refreshSession(baseUrl: string): Promise<StoredTokens | null> {
  if (inFlight) return inFlight;
  inFlight = (async () => {
    const current = getTokens();
    if (!current?.refreshToken) return null;
    try {
      const res = await globalThis.fetch(`${baseUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ refreshToken: current.refreshToken }),
      });
      if (!res.ok) {
        // 401 means the refresh token is dead (expired, logged out or reused): end the session.
        // Other failures (5xx, network) keep the tokens so a later attempt can succeed.
        if (res.status === 401) clearSession();
        await apiErrorFromResponse(res); // consumes the body; error details are not needed here
        return null;
      }
      const body = tokenSetSchema.parse(await res.json());
      const next = tokensFromApi(body.tokens);
      setTokens(next);
      return next;
    } catch {
      return null;
    } finally {
      inFlight = null;
    }
  })();
  return inFlight;
}

/** Best-effort server-side logout (revokes the refresh-token family), then clears local state. */
export async function logoutSession(baseUrl: string) {
  const current = getTokens();
  clearSession();
  if (!current?.refreshToken) return;
  try {
    await globalThis.fetch(`${baseUrl}/api/auth/logout`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ refreshToken: current.refreshToken }),
    });
  } catch {
    /* offline logout is still a logout locally */
  }
}
