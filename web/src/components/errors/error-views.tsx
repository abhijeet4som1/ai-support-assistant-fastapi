import { Trans } from '@lingui/react/macro';
import { Link, useRouter } from '@tanstack/react-router';
import { Home, RotateCcw, SearchX } from 'lucide-react';

import { toUiError, type UiError } from '@/api/errors';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { Spinner } from '@/components/ui/spinner';

function ErrorDetails({ error }: { error: UiError }) {
  return (
    <>
      <p>{error.message}</p>
      {error.kind === 'server' && error.requestId ? (
        <p className="text-xs opacity-80">
          <Trans>Request id: {error.requestId}</Trans>
        </p>
      ) : null}
    </>
  );
}

/** Route-level error component: keeps the app shell, offers retry + home. */
export function RouteErrorFallback({ error, reset }: { error: unknown; reset?: () => void }) {
  const router = useRouter();
  const ui = toUiError(error);
  const retry = () => {
    reset?.();
    void router.invalidate();
  };
  return (
    <div className="mx-auto max-w-xl space-y-4 py-10">
      <Alert variant="danger" title={<Trans>Something went wrong</Trans>}>
        <ErrorDetails error={ui} />
      </Alert>
      <div className="flex gap-2">
        <Button onClick={retry} variant="primary">
          <RotateCcw aria-hidden />
          <Trans>Try again</Trans>
        </Button>
        <Button asChild variant="outline">
          <Link to="/">
            <Home aria-hidden />
            <Trans>Go home</Trans>
          </Link>
        </Button>
      </div>
    </div>
  );
}

/** Full-page fallback for errors that escape the router (render crashes). */
export function AppCrashFallback({
  error,
  resetErrorBoundary,
}: {
  error: unknown;
  resetErrorBoundary: () => void;
}) {
  const ui = toUiError(error);
  return (
    <div className="bg-background flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md space-y-4">
        <Alert variant="danger" title={<Trans>The application hit an unexpected error</Trans>}>
          <ErrorDetails error={ui} />
        </Alert>
        <div className="flex gap-2">
          <Button onClick={resetErrorBoundary}>
            <RotateCcw aria-hidden />
            <Trans>Try again</Trans>
          </Button>
          <Button variant="outline" onClick={() => window.location.assign('/')}>
            <Home aria-hidden />
            <Trans>Reload the app</Trans>
          </Button>
        </div>
      </div>
    </div>
  );
}

export function NotFoundPage() {
  return (
    <div className="mx-auto max-w-xl py-10">
      <EmptyState
        icon={<SearchX />}
        title={<Trans>Page not found</Trans>}
        description={<Trans>The page you are looking for does not exist or was moved.</Trans>}
        action={
          <Button asChild>
            <Link to="/">
              <Trans>Go home</Trans>
            </Link>
          </Button>
        }
      />
    </div>
  );
}

export function PagePending() {
  return (
    <div className="flex justify-center py-16">
      <Spinner label="Loading…" />
    </div>
  );
}
