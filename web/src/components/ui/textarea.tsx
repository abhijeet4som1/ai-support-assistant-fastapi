import * as React from 'react';

import { cn } from '@/lib/cn';

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export function Textarea({ className, ...props }: TextareaProps) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        'bg-surface text-foreground placeholder:text-muted-foreground shadow-xs flex min-h-20 w-full rounded-md border px-3 py-2 text-sm transition-colors',
        'focus-visible:ring-ring focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-offset-1',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'aria-invalid:border-danger aria-invalid:ring-danger/30',
        className,
      )}
      {...props}
    />
  );
}
