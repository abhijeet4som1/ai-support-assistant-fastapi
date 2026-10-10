import { Trans } from '@lingui/react/macro';
import { Link } from '@tanstack/react-router';
import { History } from 'lucide-react';

import { type ConversationSummary } from '@/api/types';
import { CoverageBadge } from '@/components/chat/coverage-badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDateTime, formatRelative } from '@/lib/format';

export interface ConversationTableProps {
  conversations: ConversationSummary[];
  hasMore?: boolean;
  loadingMore?: boolean;
  onLoadMore?: () => void;
}

export function ConversationTable({
  conversations,
  hasMore,
  loadingMore,
  onLoadMore,
}: ConversationTableProps) {
  if (conversations.length === 0) {
    return (
      <EmptyState
        icon={<History />}
        title={<Trans>No conversations match</Trans>}
        description={<Trans>Try another company or clear the filters.</Trans>}
      />
    );
  }
  return (
    <div className="bg-surface overflow-hidden rounded-lg border shadow-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <Trans>Conversation</Trans>
            </TableHead>
            <TableHead>
              <Trans>Company</Trans>
            </TableHead>
            <TableHead>
              <Trans>Coverage</Trans>
            </TableHead>
            <TableHead className="text-right">
              <Trans>Messages</Trans>
            </TableHead>
            <TableHead>
              <Trans>Last activity</Trans>
            </TableHead>
            <TableHead>
              <span className="sr-only">
                <Trans>Actions</Trans>
              </span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {conversations.map((c) => (
            <TableRow key={c.id}>
              <TableCell className="max-w-xs">
                <Link
                  to="/history/$conversationId"
                  params={{ conversationId: c.id }}
                  className="text-primary block truncate font-medium hover:underline"
                >
                  {c.title || <Trans>New conversation</Trans>}
                </Link>
              </TableCell>
              <TableCell className="whitespace-nowrap">{c.companyName}</TableCell>
              <TableCell>
                <CoverageBadge coverage={c.lastCoverage} />
              </TableCell>
              <TableCell className="text-right tabular-nums">{c.messageCount}</TableCell>
              <TableCell className="whitespace-nowrap" title={formatDateTime(c.lastMessageAt)}>
                {formatRelative(c.lastMessageAt)}
              </TableCell>
              <TableCell className="text-right">
                <Button asChild variant="link" size="sm">
                  <Link to="/history/$conversationId" params={{ conversationId: c.id }}>
                    <Trans>View</Trans>
                  </Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {hasMore ? (
        <div className="flex justify-center border-t p-3">
          <Button variant="outline" size="sm" onClick={onLoadMore} loading={loadingMore}>
            <Trans>Load more</Trans>
          </Button>
        </div>
      ) : null}
    </div>
  );
}
