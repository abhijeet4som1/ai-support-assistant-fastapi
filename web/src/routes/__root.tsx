import { type QueryClient } from '@tanstack/react-query';
import { createRootRouteWithContext, Outlet } from '@tanstack/react-router';
import { Toaster } from 'sonner';

import { NotFoundPage, PagePending, RouteErrorFallback } from '@/components/errors/error-views';
import { AppHeader } from '@/components/layout/app-header';
import { NetworkBanner } from '@/components/layout/network-banner';

export interface RouterContext {
  queryClient: QueryClient;
  auth: { isAuthenticated: () => boolean };
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
  errorComponent: RouteErrorFallback,
  notFoundComponent: NotFoundPage,
  pendingComponent: PagePending,
});

function RootLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <NetworkBanner />
      <AppHeader />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
      <Toaster richColors position="top-right" />
    </div>
  );
}
