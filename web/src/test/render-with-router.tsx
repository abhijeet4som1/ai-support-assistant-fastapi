import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router';
import { render } from '@testing-library/react';

/**
 * Renders `ui` inside a throwaway router so components using <Link> work in tests.
 * The app augments TanStack's `Register` with the real router type, so a test router has to be
 * asserted once here; every test reuses this helper instead of repeating that.
 */
export function renderWithRouter(ui: React.ReactNode) {
  const rootRoute = createRootRoute({ component: () => ui });
  const router = createRouter({ routeTree: rootRoute, history: createMemoryHistory() });
  return render(
    <I18nProvider i18n={i18n}>
      <RouterProvider router={router as never} />
    </I18nProvider>,
  );
}
