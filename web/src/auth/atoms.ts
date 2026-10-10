/**
 * Auth state. Tokens are persisted (they must survive a reload); the user profile lives in memory
 * only and is loaded from the api by the authenticated layout. The optional `idToken` slot exists
 * so a future OpenID Connect provider can be plugged in without changing consumers.
 */
/* eslint-disable import-x/no-duplicates -- 'jotai' and 'jotai/utils' are distinct entry points that resolve to one stub .d.ts */
import { atom } from 'jotai';
import { atomWithStorage, createJSONStorage, RESET } from 'jotai/utils';
/* eslint-enable import-x/no-duplicates */

import { type User } from '@/api/types';
import { appStore } from '@/state/store';

export interface StoredTokens {
  accessToken: string;
  /** ISO date-time */
  accessExpiresAt: string;
  refreshToken: string;
  /** ISO date-time */
  refreshExpiresAt: string;
  idToken?: string;
}

export const TOKENS_STORAGE_KEY = 'ai-support-assistant.tokens';

const storage = createJSONStorage<StoredTokens | null>(() => localStorage);

export const tokensAtom = atomWithStorage<StoredTokens | null>(TOKENS_STORAGE_KEY, null, storage, {
  getOnInit: true,
});

export const userAtom = atom<User | null>(null);

const notExpired = (iso: string | undefined, skewMs = 0) =>
  Boolean(iso) && new Date(iso!).getTime() - skewMs > Date.now();

/** A session exists while the refresh token is still valid (the access token can be renewed). */
export const isAuthenticatedAtom = atom((get) => {
  const t = get(tokensAtom);
  return t !== null && notExpired(t.refreshExpiresAt);
});

/** True when the access token should be refreshed before use (expired or about to). */
export const accessTokenStaleAtom = atom((get) => {
  const t = get(tokensAtom);
  return t !== null && !notExpired(t.accessExpiresAt, 30_000);
});

// --- Imperative helpers for non-React code (router guard, fetch middleware) -----------------

export const getTokens = () => appStore.get(tokensAtom);
export const setTokens = (tokens: StoredTokens | null) => appStore.set(tokensAtom, tokens);
export const isAuthenticated = () => appStore.get(isAuthenticatedAtom);
export const isAccessTokenStale = () => appStore.get(accessTokenStaleAtom);
export const getUser = () => appStore.get(userAtom);
export const setUser = (user: User | null) => appStore.set(userAtom, user);

export function clearSession() {
  appStore.set(tokensAtom, RESET);
  appStore.set(userAtom, null);
}

/** Maps the api TokenSet (ISO strings from the OpenAPI client) to stored tokens. */
export function tokensFromApi(t: {
  accessToken: string;
  accessExpiresAt: string;
  refreshToken: string;
  refreshExpiresAt: string;
}): StoredTokens {
  return {
    accessToken: t.accessToken,
    accessExpiresAt: t.accessExpiresAt,
    refreshToken: t.refreshToken,
    refreshExpiresAt: t.refreshExpiresAt,
  };
}
