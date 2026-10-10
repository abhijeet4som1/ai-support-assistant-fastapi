import { cn } from '@/lib/cn';

export interface ProgressProps {
  /** 0..max */
  value: number;
  max?: number;
  label: string;
  className?: string;
}

/**
 * Native <progress> styled with classes: the one dynamic value in the app without inline styles.
 */
export function Progress({ value, max = 100, label, className }: ProgressProps) {
  return (
    <progress
      value={value}
      max={max}
      aria-label={label}
      className={cn(
        'bg-muted h-2 w-full overflow-hidden rounded-full [&::-webkit-progress-bar]:bg-transparent',
        '[&::-webkit-progress-value]:bg-primary [&::-webkit-progress-value]:rounded-full [&::-webkit-progress-value]:transition-all',
        '[&::-moz-progress-bar]:bg-primary [&::-moz-progress-bar]:rounded-full',
        className,
      )}
    />
  );
}
