import { Trans } from '@lingui/react/macro';
import { createFileRoute, Navigate, useNavigate } from '@tanstack/react-router';
import { useAtomValue } from 'jotai';

import { isAuthenticatedAtom } from '@/auth/atoms';
import { LoginForm } from '@/components/auth/login-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export const Route = createFileRoute('/login')({
  validateSearch: (search: Record<string, unknown>): { next?: string } =>
    typeof search.next === 'string' && search.next.startsWith('/') ? { next: search.next } : {},
  component: LoginPage,
});

function LoginPage() {
  const { next } = Route.useSearch();
  const authenticated = useAtomValue(isAuthenticatedAtom);
  const navigate = useNavigate();
  if (authenticated) return <Navigate to={next ?? '/chat'} replace />;
  return (
    <div className="mx-auto mt-10 max-w-md">
      <Card>
        <CardHeader>
          <CardTitle>
            <Trans>Log in</Trans>
          </CardTitle>
          <CardDescription>
            <Trans>Use one of the agent accounts to access the assistant.</Trans>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm onSuccess={() => void navigate({ to: next ?? '/chat', replace: true })} />
        </CardContent>
      </Card>
    </div>
  );
}
