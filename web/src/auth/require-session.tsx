import { useQuery } from '@tanstack/react-query';
import { useRouter } from '@tanstack/react-router';
import { useAtomValue, useSetAtom } from 'jotai';
import { useEffect } from 'react';

import { $api } from '@/api/client';
import { clearSession, isAuthenticatedAtom, userAtom } from '@/auth/atoms';
import { PagePending } from '@/components/errors/error-views';

/**
 * Renders `children` only for a live session with a loaded user profile. It is the only writer
 * of the user atom: it loads /api/auth/me once and stores the result; everything else just reads.
 *
 * When the session ends while a protected page is open (logout, refresh-token expiry, a token
 * rejected even after a refresh) it sends the user to the login page once, remembering where
 * they were. This is an effect keyed on the session flag, not a <Navigate> element: <Navigate>
 * re-navigates whenever its props change, and `location.href` changes as soon as the redirect
 * starts, so a render-time redirect nests `next=` into the login URL on every render and the
 * page never settles.
 */
export function RequireSession({ children }: { children: React.ReactNode }) {
  const authenticated = useAtomValue(isAuthenticatedAtom);
  const user = useAtomValue(userAtom);
  const setUser = useSetAtom(userAtom);
  const router = useRouter();

  const me = useQuery({
    ...$api.queryOptions('get', '/api/auth/me'),
    enabled: authenticated && user === null,
    retry: false,
    staleTime: Infinity,
  });

  useEffect(() => {
    if (me.data?.user) setUser(me.data.user);
  }, [me.data, setUser]);

  useEffect(() => {
    // The token was rejected even after a refresh attempt: end the session.
    if (me.isError) clearSession();
  }, [me.isError]);

  useEffect(() => {
    if (authenticated) return;
    const { pathname, href } = router.state.location;
    void router.navigate({
      to: '/login',
      search: pathname === '/login' ? {} : { next: href },
      replace: true,
    });
  }, [authenticated, router]);

  if (!authenticated || !user) return <PagePending />;
  return children;
}
