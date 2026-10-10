/**
 * Regression tests for the session guard. The important case is a session that ends while a
 * protected page is open (logout): the guard must redirect to the login page exactly once. An
 * earlier implementation re-navigated on every render and nested `next=` into the URL forever,
 * freezing the tab.
 *
 * The api client is stubbed: under jsdom, React Query's AbortSignal is not the one Node's Request
 * accepts, so a real query can never resolve here. The client's own tests cover the middleware.
 */
import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router';
import { act, render, screen, waitFor } from '@testing-library/react';
import { Provider as JotaiProvider } from 'jotai';

import { clearSession, setTokens } from '@/auth/atoms';
import { appStore } from '@/state/store';

import { RequireSession } from './require-session';

const me = { id: 'u1', username: 'agent1', displayName: 'Agent1' };
const meQuery = vi.hoisted(() => ({ fn: vi.fn<() => Promise<{ user: typeof me }>>() }));

vi.mock('@/api/client', () => ({
  API_BASE_URL: 'http://localhost',
  $api: { queryOptions: () => ({ queryKey: ['me'], queryFn: meQuery.fn }) },
}));

const future = (ms: number) => new Date(Date.now() + ms).toISOString();
const session = () => ({
  accessToken: 'access',
  accessExpiresAt: future(60_000),
  refreshToken: 'refresh',
  refreshExpiresAt: future(3_600_000),
});

function renderGuardedApp(initialPath: string) {
  const rootRoute = createRootRoute();
  const chatRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/chat',
    component: () => (
      <RequireSession>
        <p>secret page</p>
      </RequireSession>
    ),
  });
  const loginRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/login',
    validateSearch: (search: Record<string, unknown>): { next?: string } =>
      typeof search.next === 'string' ? { next: search.next } : {},
    component: () => <p>login page</p>,
  });
  const router = createRouter({
    routeTree: rootRoute.addChildren([chatRoute, loginRoute]),
    history: createMemoryHistory({ initialEntries: [initialPath] }),
  });
  render(
    <JotaiProvider store={appStore}>
      <I18nProvider i18n={i18n}>
        <QueryClientProvider client={new QueryClient()}>
          <RouterProvider router={router as never} />
        </QueryClientProvider>
      </I18nProvider>
    </JotaiProvider>,
  );
  return router;
}

afterEach(() => {
  clearSession();
  meQuery.fn.mockReset();
});

describe('RequireSession', () => {
  it('loads the profile and renders the protected page for a live session', async () => {
    setTokens(session());
    meQuery.fn.mockResolvedValue({ user: me });
    renderGuardedApp('/chat');
    expect(await screen.findByText('secret page')).toBeInTheDocument();
    expect(meQuery.fn).toHaveBeenCalledTimes(1);
  });

  it('redirects to login exactly once when the session ends on a protected page', async () => {
    setTokens(session());
    meQuery.fn.mockResolvedValue({ user: me });
    const router = renderGuardedApp('/chat');
    await screen.findByText('secret page');

    act(() => clearSession());

    expect(await screen.findByText('login page')).toBeInTheDocument();
    await waitFor(() => expect(router.state.location.pathname).toBe('/login'));
    // Give a runaway redirect loop the chance to show up before asserting the URL is stable.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(router.state.location.pathname).toBe('/login');
    expect(router.state.location.search).toEqual({ next: '/chat' });
    expect(router.state.location.href.match(/next=/g)).toHaveLength(1);
  });

  it('ends the session and redirects when the profile request is rejected', async () => {
    setTokens(session());
    meQuery.fn.mockRejectedValue(new Error('unauthorized'));
    const router = renderGuardedApp('/chat');
    expect(await screen.findByText('login page')).toBeInTheDocument();
    expect(router.state.location.search).toEqual({ next: '/chat' });
  });
});
