import { Trans } from '@lingui/react/macro';
import { Plus } from 'lucide-react';

import { type ConversationSummary } from '@/api/types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/cn';
import { formatRelative } from '@/lib/format';

import { CoverageBadge } from './coverage-badge';

export interface ConversationListProps {
  conversations: ConversationSummary[];
  activeId?: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  creating?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
}

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onNew,
  creating,
  hasMore,
  onLoadMore,
}: ConversationListProps) {
  return (
    <div className="space-y-2">
      <Button className="w-full" onClick={onNew} loading={creating}>
        <Plus aria-hidden />
        <Trans>New conversation</Trans>
      </Button>
      {conversations.length === 0 ? (
        <p className="text-muted-foreground px-1 pt-2 text-xs">
          <Trans>No conversations for this company yet.</Trans>
        </p>
      ) : (
        <ul className="max-h-[50vh] space-y-1 overflow-y-auto pr-1">
          {conversations.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => onSelect(c.id)}
                aria-current={c.id === activeId ? 'true' : undefined}
                className={cn(
                  'hover:bg-muted w-full rounded-md px-3 py-2 text-left text-sm transition-colors',
                  c.id === activeId &&
                    'bg-primary-soft text-primary-soft-foreground hover:bg-primary-soft',
                )}
              >
                <p className="truncate font-medium">{c.title || <Trans>New conversation</Trans>}</p>
                <p className="text-muted-foreground mt-0.5 flex items-center gap-2 text-xs">
                  <span>{formatRelative(c.lastMessageAt)}</span>
                  <span>·</span>
                  <span>{c.createdBy?.displayName}</span>
                </p>
                {c.lastCoverage ? (
                  <div className="mt-1">
                    <CoverageBadge coverage={c.lastCoverage} />
                  </div>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      )}
      {hasMore ? (
        <Button variant="ghost" size="sm" className="w-full" onClick={onLoadMore}>
          <Trans>Load more</Trans>
        </Button>
      ) : null}
    </div>
  );
}
