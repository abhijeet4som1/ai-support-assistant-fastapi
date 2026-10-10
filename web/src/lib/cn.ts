import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Compose static Tailwind class strings safely (conditional + conflict-resolving). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
