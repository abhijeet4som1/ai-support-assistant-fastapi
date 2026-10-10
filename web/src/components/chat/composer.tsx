import { Trans, useLingui } from '@lingui/react/macro';
import { MessageSquare, Send, Wrench } from 'lucide-react';
import { useState } from 'react';

import { type MessageKind } from '@/api/types';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/cn';

export interface ComposerProps {
  disabled?: boolean;
  pending?: boolean;
  onSend: (kind: MessageKind, content: string) => void;
}

export function Composer({ disabled, pending, onSend }: ComposerProps) {
  const { t } = useLingui();
  const [kind, setKind] = useState<MessageKind>('customer');
  const [text, setText] = useState('');
  const canSend = text.trim().length > 0 && !disabled && !pending;

  const submit = () => {
    if (!canSend) return;
    onSend(kind, text.trim());
    setText('');
  };

  const tab = (value: MessageKind, icon: React.ReactNode, label: React.ReactNode) => (
    <button
      type="button"
      role="tab"
      aria-selected={kind === value}
      onClick={() => setKind(value)}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors',
        kind === value
          ? 'bg-surface text-foreground shadow-xs'
          : 'text-muted-foreground hover:text-foreground',
      )}
    >
      {icon}
      {label}
    </button>
  );

  return (
    <form
      className="space-y-2"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <div
        role="tablist"
        aria-label={t`Message type`}
        className="bg-muted inline-flex gap-1 rounded-md p-1"
      >
        {tab(
          'customer',
          <MessageSquare className="size-3.5" aria-hidden />,
          <Trans>Customer message</Trans>,
        )}
        {tab(
          'instruction',
          <Wrench className="size-3.5" aria-hidden />,
          <Trans>Instruction to assistant</Trans>,
        )}
      </div>
      <div className="flex items-end gap-2">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
          }}
          disabled={disabled}
          rows={3}
          aria-label={kind === 'customer' ? t`Customer message` : t`Instruction to assistant`}
          placeholder={
            kind === 'customer'
              ? t`Paste the customer's message…`
              : t`e.g. Make it shorter, more formal, or mention the 30-day policy…`
          }
        />
        <Button type="submit" disabled={!canSend} loading={pending} aria-label={t`Send`}>
          <Send aria-hidden />
          <span className="hidden sm:inline">
            <Trans>Send</Trans>
          </span>
        </Button>
      </div>
      <p className="text-muted-foreground text-xs">
        <Trans>
          Ctrl/⌘ + Enter to send. The assistant only uses the guidelines of this company.
        </Trans>
      </p>
    </form>
  );
}
