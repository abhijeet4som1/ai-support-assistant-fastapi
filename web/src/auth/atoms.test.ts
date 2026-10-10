import {
  clearSession,
  getTokens,
  isAccessTokenStale,
  isAuthenticated,
  setTokens,
  setUser,
  TOKENS_STORAGE_KEY,
  getUser,
} from './atoms';

const iso = (ms: number) => new Date(Date.now() + ms).toISOString();
const tokens = (accessMs: number, refreshMs: number) => ({
  accessToken: 'a',
  accessExpiresAt: iso(accessMs),
  refreshToken: 'r',
  refreshExpiresAt: iso(refreshMs),
});

describe('auth atoms', () => {
  beforeEach(() => clearSession());

  it('starts logged out and persists tokens but not the user', () => {
    expect(isAuthenticated()).toBe(false);
    setTokens(tokens(60_000, 3600_000));
    setUser({ id: 'u', username: 'agent1', displayName: 'Agent1' });
    expect(isAuthenticated()).toBe(true);
    expect(localStorage.getItem(TOKENS_STORAGE_KEY)).toContain('"accessToken":"a"');
    expect(JSON.stringify(localStorage)).not.toContain('Agent1');
  });

  it('is authenticated while the refresh token lives, even if the access token expired', () => {
    setTokens(tokens(-1000, 3600_000));
    expect(isAuthenticated()).toBe(true);
    expect(isAccessTokenStale()).toBe(true);
  });

  it('treats an access token expiring within 30 s as stale', () => {
    setTokens(tokens(10_000, 3600_000));
    expect(isAccessTokenStale()).toBe(true);
    setTokens(tokens(120_000, 3600_000));
    expect(isAccessTokenStale()).toBe(false);
  });

  it('is logged out once the refresh token has expired, and clearSession wipes everything', () => {
    setTokens(tokens(60_000, -1000));
    expect(isAuthenticated()).toBe(false);
    setTokens(tokens(60_000, 3600_000));
    setUser({ id: 'u', username: 'agent1', displayName: 'Agent1' });
    clearSession();
    expect(getTokens()).toBeNull();
    expect(getUser()).toBeNull();
    expect(localStorage.getItem(TOKENS_STORAGE_KEY)).toBeNull();
  });
});
