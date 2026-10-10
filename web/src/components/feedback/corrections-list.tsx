import { Trans } from '@lingui/react/macro';
import { Link } from '@tanstack/react-router';
import { Sparkles, ThumbsDown, ThumbsUp } from 'lucide-react';

import { type Correction } from '@/api/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { formatDateTime } from '@/lib/format';

export interface CorrectionsListProps {
  corrections: Correction[];
  onToggle: (correction: Correction, active: boolean) => void;
  busyId?: string;
}

export function CorrectionsList({ corrections, onToggle, busyId }: CorrectionsListProps) {
  if (corrections.length === 0) {
    return (
      <EmptyState
        icon={<Sparkles />}
        title={<Trans>No corrections yet</Trans>}
        description={
          <Trans>
            Rate assistant answers in the chat; thumbs-down corrections show up here and guide
            future answers.
          </Trans>
        }
      />
    );
  }
  return (
    <ul className="divide-y rounded-md border">
      {corrections.map((c) => (
        <li key={c.id} className="space-y-2 px-4 py-3 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            {c.rating === 'up' ? (
              <Badge variant="success">
                <ThumbsUp aria-hidden />
                <Trans>Helpful</Trans>
              </Badge>
            ) : (
              <Badge variant="warning">
                <ThumbsDown aria-hidden />
                <Trans>Correction</Trans>
              </Badge>
            )}
            {c.active ? (
              <Badge variant="primary">
                <Trans>Active</Trans>
              </Badge>
            ) : (
              <Badge variant="neutral">
                <Trans>Inactive (guidelines changed)</Trans>
              </Badge>
            )}
            <span className="text-muted-foreground text-xs">
              {c.user?.displayName} · {formatDateTime(c.createdAt)}
            </span>
            <span className="ml-auto flex items-center gap-2">
              <Button asChild variant="link" size="sm">
                <Link to="/history/$conversationId" params={{ conversationId: c.conversationId }}>
                  <Trans>Open conversation</Trans>
                </Link>
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onToggle(c, !c.active)}
                loading={busyId === c.id}
              >
                {c.active ? <Trans>Deactivate</Trans> : <Trans>Reactivate</Trans>}
              </Button>
            </span>
          </div>
          <p className="text-muted-foreground text-xs">
            <Trans>Customer message</Trans>
          </p>
          <p className="whitespace-pre-wrap">{c.queryText}</p>
          {c.whatWasWrong ? (
            <>
              <p className="text-muted-foreground text-xs">
                <Trans>What was wrong</Trans>
              </p>
              <p className="whitespace-pre-wrap">{c.whatWasWrong}</p>
            </>
          ) : null}
          {c.correctedAnswer ? (
            <>
              <p className="text-muted-foreground text-xs">
                <Trans>Correct answer</Trans>
              </p>
              <p className="bg-success-soft/60 whitespace-pre-wrap rounded-md px-3 py-2">
                {c.correctedAnswer}
              </p>
            </>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
