import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createRouter, RouterProvider } from '@tanstack/react-router';
import { Provider as JotaiProvider } from 'jotai';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ErrorBoundary } from 'react-error-boundary';

import { toUiError } from './api/errors';
import { clearSession, isAuthenticated } from './auth/atoms';
import { AppCrashFallback } from './components/errors/error-views';
import { activateLocale, detectLocale } from './i18n';
import { routeTree } from './routeTree.gen';
import { setApiUnreachable, watchBrowserOnline } from './state/network';
import { appStore } from './state/store';
import './styles/theme.css';

/**
 * Cross-cutting reactions to api errors. A 401 that reaches here means the client middleware
 * already tried to refresh and failed, so the session is over. Network failures raise the banner.
 */
function onApiError(err: unknown) {
  const ui = toUiError(err);
  if (ui.kind === 'unauthorized') clearSession();
  setApiUnreachable(ui.kind === 'network');
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: onApiError,
    onSuccess: () => setApiUnreachable(false),
  }),
  mutationCache: new MutationCache({
    onError: onApiError,
    onSuccess: () => setApiUnreachable(false),
  }),
  defaultOptions: {
    queries: {
      retry: (failureCount, err) => toUiError(err).kind === 'network' && failureCount < 3,
      refetchOnWindowFocus: false,
      staleTime: 10_000,
    },
    mutations: { retry: 0 },
  },
});

const router = createRouter({
  routeTree,
  context: { queryClient, auth: { isAuthenticated } },
  defaultPreload: 'intent',
  scrollRestoration: true,
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

async function bootstrap() {
  await activateLocale(detectLocale());
  watchBrowserOnline();
  const rootEl = document.getElementById('root');
  if (!rootEl) throw new Error('#root not found');
  createRoot(rootEl).render(
    <StrictMode>
      <ErrorBoundary FallbackComponent={AppCrashFallback}>
        <JotaiProvider store={appStore}>
          <I18nProvider i18n={i18n}>
            <QueryClientProvider client={queryClient}>
              <RouterProvider router={router} />
            </QueryClientProvider>
          </I18nProvider>
        </JotaiProvider>
      </ErrorBoundary>
    </StrictMode>,
  );
}

void bootstrap();
