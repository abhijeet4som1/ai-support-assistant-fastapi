import { Trans, useLingui } from '@lingui/react/macro';
import {
  AlertOctagon,
  BookOpen,
  Check,
  Copy,
  ListChecks,
  MessageCircleQuestion,
  RotateCcw,
  Scale,
} from 'lucide-react';
import { useState } from 'react';

import { type Message } from '@/api/types';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

import { CoverageBadge } from './coverage-badge';

export interface AssistantMessageProps {
  message: Message;
  onRetry?: () => void;
  retrying?: boolean;
  /** Slot for feedback controls (thumbs), rendered in the footer. */
  footer?: React.ReactNode;
}

export function AssistantMessage({ message, onRetry, retrying, footer }: AssistantMessageProps) {
  const { t } = useLingui();
  const [copied, setCopied] = useState(false);
  const g = message.guidance;

  if (message.status === 'failed' || !g) {
    return (
      <Alert variant="danger" title={<Trans>The assistant could not answer</Trans>}>
        <p>{message.error ?? t`Unknown error`}</p>
        {onRetry ? (
          <Button size="sm" variant="outline" className="mt-2" onClick={onRetry} loading={retrying}>
            <RotateCcw aria-hidden />
            <Trans>Retry</Trans>
          </Button>
        ) : null}
      </Alert>
    );
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(g.recommendedReply ?? '');
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div
      className="bg-surface shadow-xs space-y-4 rounded-lg border p-4"
      data-testid="assistant-message"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <CoverageBadge coverage={g.coverage} />
        <span className="text-muted-foreground text-xs">
          {message.model} · {message.latencyMs ? `${(message.latencyMs / 1000).toFixed(1)} s` : ''}
        </span>
      </div>

      {g.escalation?.recommended ? (
        <Alert variant="warning" title={<Trans>Escalation recommended</Trans>}>
          <p>
            {g.escalation.reason}
            {g.escalation.to ? (
              <>
                {' '}
                <Trans>→ {g.escalation.to}</Trans>
              </>
            ) : null}
          </p>
        </Alert>
      ) : null}

      {g.handlingSteps?.length ? (
        <section>
          <h3 className="text-muted-foreground mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide">
            <ListChecks className="size-3.5" aria-hidden />
            <Trans>Handling steps</Trans>
          </h3>
          <ol className="list-decimal space-y-1 pl-5 text-sm">
            {g.handlingSteps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </section>
      ) : null}

      {g.clarifications?.length ? (
        <section>
          <h3 className="text-muted-foreground mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide">
            <MessageCircleQuestion className="size-3.5" aria-hidden />
            <Trans>Clarify with the customer</Trans>
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {g.clarifications.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {g.agentDecisions?.length ? (
        <section>
          <h3 className="text-muted-foreground mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide">
            <Scale className="size-3.5" aria-hidden />
            <Trans>Your call</Trans>
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {g.agentDecisions.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section>
        <div className="mb-1.5 flex items-start justify-between gap-2">
          <div>
            <h3 className="text-muted-foreground text-xs font-semibold uppercase tracking-wide">
              <Trans>Recommended reply</Trans>
            </h3>
            {g.clarifications?.length ? (
              <p className="text-muted-foreground text-xs">
                <Trans>This reply asks the customer the questions above.</Trans>
              </p>
            ) : g.handlingSteps?.length ? (
              <p className="text-muted-foreground text-xs">
                <Trans>Send this to the customer once the steps above are done.</Trans>
              </p>
            ) : null}
          </div>
          <Button size="sm" variant="ghost" onClick={() => void copy()}>
            {copied ? <Check aria-hidden /> : <Copy aria-hidden />}
            {copied ? <Trans>Copied</Trans> : <Trans>Copy</Trans>}
          </Button>
        </div>
        <p className="bg-primary-soft/50 whitespace-pre-wrap rounded-md px-3 py-2 text-sm">
          {g.recommendedReply}
        </p>
      </section>

      {g.notes ? (
        <p className="text-muted-foreground flex items-start gap-1.5 text-xs">
          <AlertOctagon className="mt-0.5 size-3.5 shrink-0" aria-hidden />
          {g.notes}
        </p>
      ) : null}

      {g.citations?.length ? (
        <details className="text-xs">
          <summary className="text-muted-foreground flex cursor-pointer items-center gap-1.5">
            <BookOpen className="size-3.5" aria-hidden />
            <Trans>Based on {g.citations.length} guideline sections</Trans>
          </summary>
          <ul className="mt-1.5 flex flex-wrap gap-1.5">
            {g.citations.map((c) => (
              <li key={c.chunkId} className="bg-muted rounded-full px-2 py-0.5">
                {c.title ?? c.chunkId}
              </li>
            ))}
          </ul>
        </details>
      ) : null}

      {footer ? <div className="border-t pt-3">{footer}</div> : null}
    </div>
  );
}
