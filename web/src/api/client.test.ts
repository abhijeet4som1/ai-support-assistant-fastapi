/**
 * Proves the api client adds the bearer token and turns modelled error responses into ApiError
 * with the error name taken from X-Amzn-Errortype.
 */
import { clearSession, getTokens, setTokens } from '@/auth/atoms';
import { errorResponse, installFetchMock, jsonResponse } from '@/test/setup-fetch';

import { ApiError } from './api-error';
import { apiClient } from './client';

const me = { id: 'u1', username: 'agent1', displayName: 'Agent1' };
const future = (ms: number) => new Date(Date.now() + ms).toISOString();
const session = (accessToken: string, accessMs = 60_000) => ({
  accessToken,
  accessExpiresAt: future(accessMs),
  refreshToken: 'refresh-1',
  refreshExpiresAt: future(7 * 24 * 3600_000),
});

describe('api client', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    clearSession();
  });

  it('sends the bearer token when logged in and none otherwise', async () => {
    const mock = installFetchMock(() => jsonResponse({ items: [] }));
    await apiClient.GET('/api/companies');
    expect(mock.calls[0]!.req.headers.get('authorization')).toBeNull();

    setTokens(session('secret-token'));
    await apiClient.GET('/api/companies');
    expect(mock.calls[1]!.req.headers.get('authorization')).toBe('Bearer secret-token');
    expect(new URL(mock.calls[1]!.req.url).pathname).toBe('/api/companies');
  });

  it('serialises JSON bodies and path/query params', async () => {
    const mock = installFetchMock(() => jsonResponse({ items: [], nextCursor: undefined }));
    await apiClient.GET('/api/conversations', {
      params: { query: { companyId: 'c1', coverage: 'covered', limit: 5 } },
    });
    const url = new URL(mock.calls[0]!.req.url);
    expect(url.pathname).toBe('/api/conversations');
    expect(url.searchParams.get('companyId')).toBe('c1');
    expect(url.searchParams.get('coverage')).toBe('covered');
    expect(url.searchParams.get('limit')).toBe('5');
    await apiClient.POST('/api/auth/login', { body: { username: 'agent1', password: 'pw' } });
    expect(mock.calls[1]!.body).toEqual({ username: 'agent1', password: 'pw' });
    expect(mock.calls[1]!.req.headers.get('content-type')).toMatch(/application\/json/);
  });

  it('refreshes once and replays the request when the access token is rejected', async () => {
    setTokens(session('stale-token'));
    let refreshes = 0;
    const mock = installFetchMock((req) => {
      const path = new URL(req.url).pathname;
      if (path === '/api/auth/refresh') {
        refreshes++;
        return jsonResponse({ tokens: session('fresh-token'), user: me });
      }
      if (req.headers.get('authorization') === 'Bearer fresh-token')
        return jsonResponse({ items: [] });
      return errorResponse('UnauthorizedError', 401, { message: 'expired' });
    });
    // Two concurrent calls share a single refresh.
    const [a, b] = await Promise.all([
      apiClient.GET('/api/companies'),
      apiClient.GET('/api/conversations'),
    ]);
    expect(a.data).toEqual({ items: [] });
    expect(b.data).toEqual({ items: [] });
    expect(refreshes).toBe(1);
    expect(
      mock.calls.filter((c) => new URL(c.req.url).pathname === '/api/auth/refresh'),
    ).toHaveLength(1);
    expect(getTokens()?.accessToken).toBe('fresh-token');
  });

  it('refreshes proactively when the access token is about to expire', async () => {
    setTokens(session('almost-expired', 5_000));
    const mock = installFetchMock((req) =>
      new URL(req.url).pathname === '/api/auth/refresh'
        ? jsonResponse({ tokens: session('renewed'), user: me })
        : jsonResponse({ items: [] }),
    );
    await apiClient.GET('/api/companies');
    expect(new URL(mock.calls[0]!.req.url).pathname).toBe('/api/auth/refresh');
    expect(mock.calls[1]!.req.headers.get('authorization')).toBe('Bearer renewed');
  });

  it('ends the session when the refresh token is rejected', async () => {
    setTokens(session('stale-token'));
    installFetchMock((req) =>
      new URL(req.url).pathname === '/api/auth/refresh'
        ? errorResponse('UnauthorizedError', 401, { message: 'reused' })
        : errorResponse('UnauthorizedError', 401, { message: 'expired' }),
    );
    const err = await apiClient.GET('/api/companies').catch((e: unknown) => e);
    if (!(err instanceof ApiError)) throw new Error('expected ApiError');
    expect(err.status).toBe(401);
    expect(getTokens()).toBeNull();
  });

  it('throws ApiError with the modelled type, request id and body for non-2xx responses', async () => {
    installFetchMock(() =>
      errorResponse('GuidelinesConflictError', 409, {
        message: 'newer version exists',
        latestVersionId: 'v9',
      }),
    );
    const err = await apiClient.GET('/api/companies').catch((e: unknown) => e);
    if (!(err instanceof ApiError)) throw new Error('expected ApiError');
    const apiErr = err;
    expect(apiErr.status).toBe(409);
    expect(apiErr.type).toBe('GuidelinesConflictError');
    expect(apiErr.requestId).toBe('test-req');
    expect(apiErr.message).toBe('newer version exists');
    expect(apiErr.body.latestVersionId).toBe('v9');
  });
});
