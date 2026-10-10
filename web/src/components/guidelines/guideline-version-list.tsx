import { Trans, useLingui } from '@lingui/react/macro';
import { CheckCircle2, History, RotateCcw } from 'lucide-react';

import { isProcessing } from '@/api/guidelines';
import { type GuidelineVersionSummary } from '@/api/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatBytes, formatDateTime } from '@/lib/format';

export interface GuidelineVersionListProps {
  versions: GuidelineVersionSummary[];
  onActivate?: (id: string) => void;
  onRetry?: (id: string) => void;
  busyId?: string;
}

function StatusBadge({ v }: { v: GuidelineVersionSummary }) {
  const { t } = useLingui();
  if (v.isActive) {
    return (
      <Badge variant="success">
        <CheckCircle2 aria-hidden />
        <Trans>Active</Trans>
      </Badge>
    );
  }
  const labels: Record<string, [string, 'neutral' | 'primary' | 'danger' | 'warning']> = {
    ready: [t`Ready`, 'neutral'],
    failed: [t`Failed`, 'danger'],
    superseded: [t`Superseded`, 'neutral'],
    queued: [t`Queued`, 'primary'],
    parsing: [t`Processing`, 'primary'],
    chunking: [t`Processing`, 'primary'],
    embedding: [t`Processing`, 'primary'],
  };
  const [label, variant] = labels[v.status ?? ''] ?? [v.status ?? '', 'neutral'];
  return <Badge variant={variant}>{label}</Badge>;
}

export function GuidelineVersionList({
  versions,
  onActivate,
  onRetry,
  busyId,
}: GuidelineVersionListProps) {
  if (versions.length === 0) {
    return (
      <p className="text-muted-foreground flex items-center gap-2 text-sm">
        <History className="size-4" aria-hidden />
        <Trans>No uploads yet.</Trans>
      </p>
    );
  }
  return (
    <ul className="divide-y rounded-md border">
      {versions.map((v) => (
        <li key={v.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 text-sm">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="truncate font-medium">{v.filename}</span>
              <StatusBadge v={v} />
            </div>
            <p className="text-muted-foreground mt-0.5 text-xs">
              <Trans>
                {formatBytes(v.sizeBytes)} · uploaded by {v.uploadedBy?.displayName ?? '—'} on{' '}
                {formatDateTime(v.createdAt)}
                {v.chunksTotal ? ` · ${v.chunksTotal} sections` : ''}
              </Trans>
            </p>
            {v.status === 'failed' && v.error ? (
              <p className="text-danger mt-1 text-xs">{v.error}</p>
            ) : null}
          </div>
          <div className="flex shrink-0 gap-2">
            {v.status === 'ready' && !v.isActive && onActivate ? (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onActivate(v.id)}
                loading={busyId === v.id}
              >
                <Trans>Make active</Trans>
              </Button>
            ) : null}
            {v.status === 'failed' && onRetry ? (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onRetry(v.id)}
                loading={busyId === v.id}
              >
                <RotateCcw aria-hidden />
                <Trans>Retry</Trans>
              </Button>
            ) : null}
            {isProcessing(v.status) ? (
              <span className="text-muted-foreground text-xs">
                {v.chunksTotal ? `${v.chunksEmbedded ?? 0}/${v.chunksTotal}` : ''}
              </span>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
