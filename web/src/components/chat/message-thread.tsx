import { Trans } from '@lingui/react/macro';
import { Bot, History, MessageSquareText, User, Wrench } from 'lucide-react';
import { useEffect, useRef } from 'react';

import { type Message } from '@/api/types';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import { formatDateTime } from '@/lib/format';

import { AssistantMessage } from './assistant-message';

export interface MessageThreadProps {
  messages: Message[];
  pending?: boolean;
  onRetry?: (message: Message) => void;
  retrying?: boolean;
  renderFeedback?: (message: Message) => React.ReactNode;
  /** Older messages exist beyond the loaded page; `onLoadOlder` prepends the next page. */
  hasOlder?: boolean;
  onLoadOlder?: () => void;
  loadingOlder?: boolean;
}

export function MessageThread({
  messages,
  pending,
  onRetry,
  retrying,
  renderFeedback,
  hasOlder,
  onLoadOlder,
  loadingOlder,
}: MessageThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);
  // Scroll to the newest message when one is appended or the assistant starts thinking, but not
  // when older messages are prepended above the current view.
  const lastId = messages.at(-1)?.id;
  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: 'end' });
  }, [lastId, pending]);

  if (messages.length === 0 && !pending) {
    return (
      <div className="text-muted-foreground flex h-full flex-col items-center justify-center gap-2 py-16 text-center text-sm">
        <MessageSquareText className="size-8" aria-hidden />
        <p>
          <Trans>Paste the customer message below to get a recommended reply.</Trans>
        </p>
      </div>
    );
  }

  return (
    <ol className="space-y-4">
      {hasOlder ? (
        <li className="flex justify-center">
          <Button variant="outline" size="sm" onClick={onLoadOlder} disabled={loadingOlder}>
            {loadingOlder ? <Spinner /> : <History aria-hidden />}
            <Trans>Load earlier messages</Trans>
          </Button>
        </li>
      ) : null}
      {messages.map((m, i) => {
        const previousUser = i > 0 ? messages[i - 1] : undefined;
        if (m.role === 'assistant') {
          return (
            <li key={m.id} className="flex gap-3">
              <span className="bg-primary text-primary-foreground mt-1 flex size-8 shrink-0 items-center justify-center rounded-full">
                <Bot className="size-4" aria-hidden />
              </span>
              <div className="min-w-0 flex-1">
                <AssistantMessage
                  message={m}
                  retrying={retrying}
                  onRetry={
                    onRetry && previousUser && previousUser.role !== 'assistant'
                      ? () => onRetry(previousUser)
                      : undefined
                  }
                  footer={renderFeedback?.(m)}
                />
              </div>
            </li>
          );
        }
        const isInstruction = m.role === 'instruction';
        return (
          <li key={m.id} className="flex justify-end gap-3">
            <div className="max-w-[80%]">
              <div
                className={
                  isInstruction
                    ? 'bg-warning-soft text-warning-soft-foreground whitespace-pre-wrap rounded-lg rounded-br-none px-4 py-2 text-sm'
                    : 'bg-muted text-foreground whitespace-pre-wrap rounded-lg rounded-br-none px-4 py-2 text-sm'
                }
              >
                {isInstruction ? (
                  <span className="mb-1 flex items-center gap-1 text-xs font-medium">
                    <Wrench className="size-3" aria-hidden />
                    <Trans>Instruction to assistant</Trans>
                  </span>
                ) : null}
                {m.content}
              </div>
              <p className="text-muted-foreground mt-1 text-right text-xs">
                {m.createdBy?.displayName} · {formatDateTime(m.createdAt)}
              </p>
            </div>
            <span className="bg-primary-soft text-primary mt-1 flex size-8 shrink-0 items-center justify-center rounded-full">
              <User className="size-4" aria-hidden />
            </span>
          </li>
        );
      })}
      {pending ? (
        <li className="flex gap-3">
          <span className="bg-primary text-primary-foreground mt-1 flex size-8 shrink-0 items-center justify-center rounded-full">
            <Bot className="size-4" aria-hidden />
          </span>
          <div className="bg-surface rounded-lg border px-4 py-3">
            <Spinner label="Thinking…" />
          </div>
        </li>
      ) : null}
      <div ref={endRef} />
    </ol>
  );
}
