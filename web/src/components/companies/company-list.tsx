import { Trans } from '@lingui/react/macro';
import { Link } from '@tanstack/react-router';
import { Building2, ChevronRight, MessageSquare } from 'lucide-react';

import { type Company } from '@/api/types';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';

import { GuidelineStatusBadge } from './guideline-status-badge';

export function CompanyList({ companies }: { companies: Company[] }) {
  if (companies.length === 0) {
    return (
      <EmptyState
        icon={<Building2 />}
        title={<Trans>No companies yet</Trans>}
        description={
          <Trans>
            Add a company and upload its support guidelines to start chatting on its behalf.
          </Trans>
        }
        action={
          <Button asChild>
            <Link to="/companies/new">
              <Trans>Add company</Trans>
            </Link>
          </Button>
        }
      />
    );
  }
  return (
    <ul className="bg-surface divide-y overflow-hidden rounded-lg border shadow-sm">
      {companies.map((c) => (
        <li key={c.id}>
          <Link
            to="/companies/$companyId"
            params={{ companyId: c.id }}
            className="hover:bg-muted/60 flex items-center gap-4 px-4 py-4 transition-colors sm:px-6"
          >
            <div className="bg-primary-soft text-primary flex size-12 shrink-0 items-center justify-center rounded-full">
              <Building2 className="size-5" aria-hidden />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-primary truncate text-sm font-medium">{c.name}</p>
                <GuidelineStatusBadge active={c.activeGuidelines} latest={c.latestGuidelines} />
              </div>
              <p className="text-muted-foreground mt-0.5 truncate text-sm">
                {c.description ? c.description : <Trans>No description</Trans>}
              </p>
            </div>
            <div className="text-muted-foreground hidden shrink-0 items-center gap-1.5 text-sm sm:flex">
              <MessageSquare className="size-4" aria-hidden />
              <Trans>{c.conversationCount ?? 0} conversations</Trans>
            </div>
            <ChevronRight className="text-muted-foreground size-5 shrink-0" aria-hidden />
          </Link>
        </li>
      ))}
    </ul>
  );
}
