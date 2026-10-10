import { Trans } from '@lingui/react/macro';
import { ChevronDown } from 'lucide-react';
import { useState } from 'react';

import { type GuidelineChunk, type GuidelineVersionSummary } from '@/api/types';
import { Button } from '@/components/ui/button';
import { formatDateTime } from '@/lib/format';

export interface GuidelineViewerProps {
  version: GuidelineVersionSummary;
  text: string;
  chunks: GuidelineChunk[];
}

/** Shows the active guidelines as the assistant sees them: one section per chunk. */
export function GuidelineViewer({ version, text, chunks }: GuidelineViewerProps) {
  const [showRaw, setShowRaw] = useState(false);
  return (
    <div className="space-y-4">
      <p className="text-muted-foreground text-sm">
        <Trans>
          Active file <span className="text-foreground font-medium">{version.filename}</span>,
          processed on {formatDateTime(version.readyAt ?? version.updatedAt)} into {chunks.length}{' '}
          sections.
        </Trans>
      </p>
      <ul className="divide-y rounded-md border">
        {chunks.map((c) => (
          <li key={c.id}>
            <details className="group">
              <summary className="hover:bg-muted/60 flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-2.5 text-sm">
                <span className="font-medium">
                  {c.title ?? <Trans>Section {(c.ordinal ?? 0) + 1}</Trans>}
                </span>
                <span className="text-muted-foreground flex items-center gap-2 text-xs">
                  <Trans>{c.tokenCount} tokens</Trans>
                  <ChevronDown
                    className="size-4 transition-transform group-open:rotate-180"
                    aria-hidden
                  />
                </span>
              </summary>
              <pre className="bg-muted/40 text-foreground max-h-80 overflow-auto whitespace-pre-wrap px-4 py-3 font-sans text-sm">
                {c.content}
              </pre>
            </details>
          </li>
        ))}
      </ul>
      <div>
        <Button variant="link" size="sm" className="px-0" onClick={() => setShowRaw((v) => !v)}>
          {showRaw ? <Trans>Hide extracted text</Trans> : <Trans>Show extracted text</Trans>}
        </Button>
        {showRaw ? (
          <pre className="bg-muted/40 mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded-md border px-4 py-3 font-sans text-sm">
            {text}
          </pre>
        ) : null}
      </div>
    </div>
  );
}
