import createFetchClient, { type Middleware } from 'openapi-fetch';
import createQueryClient from 'openapi-react-query';

import { getTokens, isAccessTokenStale } from '@/auth/atoms';

import { apiErrorFromResponse } from './api-error';
import { refreshSession } from './session';

import type { paths } from './schema';

export const API_BASE_URL =
  typeof window === 'undefined' ? 'http://localhost' : window.location.origin;

const AUTH_PATHS = ['/api/auth/login', '/api/auth/refresh', '/api/auth/logout'];
const isAuthCall = (request: Request) => AUTH_PATHS.includes(new URL(request.url).pathname);

/** Requests that may have to be replayed after a refresh, keyed by openapi-fetch's request id. */
const replayable = new Map<string, Request>();

/**
 * 1. Attaches the bearer token, refreshing it first when it is (about to be) expired.
 * 2. Turns every non-2xx response into a thrown ApiError.
 * 3. On a 401 for a protected call, refreshes once (single-flight) and replays the request.
 */
const authAndErrors: Middleware = {
  async onRequest({ request, id }) {
    if (isAuthCall(request)) return request;
    if (isAccessTokenStale() && getTokens()?.refreshToken) await refreshSession(API_BASE_URL);
    const token = getTokens()?.accessToken;
    if (token && !request.headers.has('authorization')) {
      request.headers.set('authorization', `Bearer ${token}`);
    }
    replayable.set(id, request.clone());
    return request;
  },
  async onResponse({ request, response, id }) {
    const original = replayable.get(id);
    replayable.delete(id);
    if (response.ok) return response;

    if (response.status === 401 && !isAuthCall(request) && original && getTokens()?.refreshToken) {
      const refreshed = await refreshSession(API_BASE_URL);
      if (refreshed) {
        const retry = new Request(original, { headers: new Headers(original.headers) });
        retry.headers.set('authorization', `Bearer ${refreshed.accessToken}`);
        const replayed = await globalThis.fetch(retry);
        if (replayed.ok) return replayed;
        throw await apiErrorFromResponse(replayed);
      }
    }
    throw await apiErrorFromResponse(response);
  },
  onError({ id }) {
    replayable.delete(id);
  },
};

/**
 * Typed fetch client generated from the OpenAPI document (which is generated from the Smithy
 * model). Same-origin: nginx proxies /api. `fetch` is resolved at call time so tests can stub it.
 */
export const apiClient = createFetchClient<paths>({
  baseUrl: API_BASE_URL,
  fetch: (input) => globalThis.fetch(input),
});
apiClient.use(authAndErrors);

/** React Query bindings: `$api.useQuery('get', '/api/companies')`, `$api.queryOptions(...)`, ... */
export const $api = createQueryClient(apiClient);
