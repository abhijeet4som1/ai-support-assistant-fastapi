import { createFileRoute, Outlet, redirect } from '@tanstack/react-router';

import { RequireSession } from '@/auth/require-session';

/**
 * Guard for everything that needs a session. `beforeLoad` rejects direct navigation without a
 * session before any loader runs; <RequireSession> loads the user profile and handles a session
 * that ends while a protected page is already open.
 */
export const Route = createFileRoute('/_authenticated')({
  beforeLoad: ({ context, location }) => {
    if (!context.auth.isAuthenticated()) {
      throw redirect({ to: '/login', search: { next: location.href } });
    }
  },
  component: () => (
    <RequireSession>
      <Outlet />
    </RequireSession>
  ),
});
