import { Trans, useLingui } from '@lingui/react/macro';
import { RotateCcw } from 'lucide-react';

import { isProcessing } from '@/api/guidelines';
import { type GuidelineVersionSummary } from '@/api/types';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

const STAGE_ORDER = ['queued', 'parsing', 'chunking', 'embedding'] as const;

export function GuidelineProgress({
  version,
  onRetry,
  retrying,
}: {
  version: GuidelineVersionSummary;
  onRetry?: () => void;
  retrying?: boolean;
}) {
  const { t } = useLingui();
  const stageLabel: Record<string, string> = {
    queued: t`Queued`,
    parsing: t`Extracting text`,
    chunking: t`Splitting into sections`,
    embedding: t`Indexing sections`,
  };

  if (version.status === 'failed') {
    return (
      <Alert variant="danger" title={<Trans>Processing failed</Trans>}>
        <p>{version.error ?? t`Unknown error`}</p>
        {onRetry ? (
          <Button size="sm" variant="outline" className="mt-2" onClick={onRetry} loading={retrying}>
            <RotateCcw aria-hidden />
            <Trans>Retry</Trans>
          </Button>
        ) : null}
      </Alert>
    );
  }
  if (!isProcessing(version.status)) return null;

  const stageIndex = STAGE_ORDER.findIndex((stage) => stage === version.status);
  const embedPct = version.chunksTotal
    ? ((version.chunksEmbedded ?? 0) / version.chunksTotal) * 100
    : 0;
  // Stages before embedding are quick; give them 5% each so the bar moves immediately.
  const percent =
    version.status === 'embedding' ? 15 + embedPct * 0.85 : Math.max(2, stageIndex * 5);

  return (
    <div className="space-y-2" data-testid="guideline-progress">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{stageLabel[version.status ?? ''] ?? version.status}</span>
        <span className="text-muted-foreground">
          {version.status === 'embedding' ? (
            <Trans>
              {version.chunksEmbedded ?? 0} of {version.chunksTotal ?? 0} sections
            </Trans>
          ) : (
            <Trans>Processing…</Trans>
          )}
        </span>
      </div>
      <Progress value={Math.round(percent)} label={t`Guideline processing progress`} />
      <p className="text-muted-foreground text-xs">
        <Trans>You can keep working; this page updates automatically.</Trans>
      </p>
    </div>
  );
}
