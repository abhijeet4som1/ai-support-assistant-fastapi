import { Trans } from '@lingui/react/macro';
import { AlertTriangle, CheckCircle2, FileQuestion, Loader2 } from 'lucide-react';

import { type GuidelineVersionSummary } from '@/api/types';
import { Badge } from '@/components/ui/badge';
import { formatRelative } from '@/lib/format';

const PROCESSING = new Set(['queued', 'parsing', 'chunking', 'embedding']);

/** One-line status of a company's guidelines, driven by the active + latest version. */
export function GuidelineStatusBadge({
  active,
  latest,
}: {
  active?: GuidelineVersionSummary;
  latest?: GuidelineVersionSummary;
}) {
  if (latest && PROCESSING.has(latest.status ?? '')) {
    const pct = latest.chunksTotal
      ? Math.round(((latest.chunksEmbedded ?? 0) / latest.chunksTotal) * 100)
      : 0;
    return (
      <Badge variant="primary">
        <Loader2 className="animate-spin" aria-hidden />
        {latest.status === 'embedding' ? (
          <Trans>Processing {pct}%</Trans>
        ) : (
          <Trans>Processing</Trans>
        )}
      </Badge>
    );
  }
  if (latest?.status === 'failed' && !active) {
    return (
      <Badge variant="danger">
        <AlertTriangle aria-hidden />
        <Trans>Processing failed</Trans>
      </Badge>
    );
  }
  if (active) {
    return (
      <Badge variant="success">
        <CheckCircle2 aria-hidden />
        <Trans>Guidelines updated {formatRelative(active.readyAt ?? active.createdAt)}</Trans>
      </Badge>
    );
  }
  return (
    <Badge variant="warning">
      <FileQuestion aria-hidden />
      <Trans>No guidelines yet</Trans>
    </Badge>
  );
}
