import { Trans } from '@lingui/react/macro';
import { Cpu, FileSearch, Sparkles } from 'lucide-react';

import { type Message } from '@/api/types';
import { Badge } from '@/components/ui/badge';

/** Explains an assistant turn: which sections were retrieved, corrections used, model stats. */
export function WhyPanel({ message }: { message: Message }) {
  if (message.role !== 'assistant') return null;
  const retrieval = message.retrieval ?? [];
  const corrections = message.correctionsUsed ?? [];
  return (
    <details className="text-xs">
      <summary className="text-muted-foreground flex cursor-pointer items-center gap-1.5">
        <FileSearch className="size-3.5" aria-hidden />
        <Trans>Why this answer</Trans>
      </summary>
      <div className="mt-2 space-y-3">
        <div>
          <p className="mb-1 font-medium">
            <Trans>Retrieved guideline sections</Trans>
          </p>
          {retrieval.length === 0 ? (
            <p className="text-muted-foreground">
              <Trans>
                None above the relevance threshold, so the assistant reported the topic as not
                covered.
              </Trans>
            </p>
          ) : (
            <ul className="space-y-1">
              {retrieval.map((r) => (
                <li key={r.chunkId} className="flex items-center justify-between gap-3">
                  <span className="truncate">{r.title ?? r.chunkId}</span>
                  <Badge variant="neutral">{Math.round((r.score ?? 0) * 100)}%</Badge>
                </li>
              ))}
            </ul>
          )}
        </div>
        {corrections.length ? (
          <div>
            <p className="mb-1 flex items-center gap-1 font-medium">
              <Sparkles className="size-3.5" aria-hidden />
              <Trans>Corrections used</Trans>
            </p>
            <ul className="space-y-1">
              {corrections.map((c) => (
                <li key={c.correctionId} className="flex items-center justify-between gap-3">
                  <span className="truncate">{c.correctionId}</span>
                  <Badge variant="neutral">{Math.round((c.score ?? 0) * 100)}%</Badge>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <p className="text-muted-foreground flex flex-wrap items-center gap-x-3 gap-y-1">
          <Cpu className="size-3.5" aria-hidden />
          <span>{message.model}</span>
          {message.promptTokens !== undefined ? (
            <span>
              <Trans>{message.promptTokens} prompt tokens</Trans>
            </span>
          ) : null}
          {message.thinkingTokens !== undefined ? (
            <span>
              <Trans>{message.thinkingTokens} thinking tokens</Trans>
            </span>
          ) : null}
          {message.completionTokens !== undefined ? (
            <span>
              <Trans>{message.completionTokens} output tokens</Trans>
            </span>
          ) : null}
          {message.totalTokens !== undefined ? (
            <span className="font-medium">
              <Trans>{message.totalTokens} total tokens</Trans>
            </span>
          ) : null}
          {message.latencyMs !== undefined ? (
            <span>{(message.latencyMs / 1000).toFixed(1)} s</span>
          ) : null}
          {message.guidelineVersionId ? (
            <span>
              <Trans>guidelines v. {message.guidelineVersionId.slice(0, 8)}</Trans>
            </span>
          ) : null}
        </p>
      </div>
    </details>
  );
}
