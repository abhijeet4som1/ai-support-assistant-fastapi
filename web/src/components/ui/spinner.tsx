import { Loader2 } from 'lucide-react';

import { cn } from '@/lib/cn';

export function Spinner({ className, label }: { className?: string; label?: string }) {
  return (
    <span
      role="status"
      className={cn('text-muted-foreground inline-flex items-center gap-2', className)}
    >
      <Loader2 className="size-4 animate-spin" aria-hidden />
      {label ? <span className="text-sm">{label}</span> : <span className="sr-only">Loading</span>}
    </span>
  );
}
