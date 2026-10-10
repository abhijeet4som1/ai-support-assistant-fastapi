import { Trans, useLingui } from '@lingui/react/macro';
import { Link, useNavigate } from '@tanstack/react-router';
import { useAtomValue } from 'jotai';
import { Building2, History, LogOut, MessageSquare } from 'lucide-react';

import { API_BASE_URL } from '@/api/client';
import { logoutSession } from '@/api/session';
import { isAuthenticatedAtom, userAtom } from '@/auth/atoms';
import { Button } from '@/components/ui/button';
import { activateLocale, isLocale, LOCALES } from '@/i18n';

const navLinkClass =
  'text-muted-foreground hover:border-border hover:text-foreground inline-flex items-center gap-2 border-b-2 border-transparent px-1 pt-1 text-sm font-medium transition-colors';
const activeProps = { className: 'border-primary text-foreground' };

export function AppHeader() {
  const authenticated = useAtomValue(isAuthenticatedAtom);
  const user = useAtomValue(userAtom);
  const navigate = useNavigate();
  const { i18n, t } = useLingui();

  const logout = async () => {
    await logoutSession(API_BASE_URL);
    await navigate({ to: '/login' });
  };

  return (
    <header className="bg-surface shadow-xs sticky top-0 z-10 border-b">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-primary text-xl font-bold">
            <Trans>AI Support Assistant</Trans>
          </Link>
          {authenticated ? (
            <nav aria-label={t`Main`} className="hidden h-16 items-stretch gap-6 sm:flex">
              <Link to="/chat" className={navLinkClass} activeProps={activeProps}>
                <MessageSquare className="size-4" aria-hidden />
                <Trans>Chat</Trans>
              </Link>
              <Link to="/history" className={navLinkClass} activeProps={activeProps}>
                <History className="size-4" aria-hidden />
                <Trans>History</Trans>
              </Link>
              <Link to="/companies" className={navLinkClass} activeProps={activeProps}>
                <Building2 className="size-4" aria-hidden />
                <Trans>Companies</Trans>
              </Link>
            </nav>
          ) : null}
        </div>
        <div className="flex items-center gap-3">
          <label className="sr-only" htmlFor="locale">
            <Trans>Language</Trans>
          </label>
          <select
            id="locale"
            className="bg-surface text-muted-foreground h-8 rounded-md border px-2 text-xs"
            value={i18n.locale}
            onChange={(e) => {
              if (isLocale(e.target.value)) void activateLocale(e.target.value);
            }}
          >
            {LOCALES.map((l) => (
              <option key={l} value={l}>
                {l.toUpperCase()}
              </option>
            ))}
          </select>
          {authenticated ? (
            <>
              <span className="text-muted-foreground hidden text-sm sm:inline">
                {user?.displayName}
              </span>
              <Button variant="ghost" size="sm" onClick={() => void logout()}>
                <LogOut aria-hidden />
                <Trans>Log out</Trans>
              </Button>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
