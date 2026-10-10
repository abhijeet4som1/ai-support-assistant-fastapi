import { i18n } from '@lingui/core';

export function formatDateTime(date: Date | string | undefined | null) {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(i18n.locale, { dateStyle: 'medium', timeStyle: 'short' }).format(
    d,
  );
}

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 365 * 24 * 3600],
  ['month', 30 * 24 * 3600],
  ['week', 7 * 24 * 3600],
  ['day', 24 * 3600],
  ['hour', 3600],
  ['minute', 60],
];

export function formatRelative(date: Date | string | undefined | null, now = Date.now()) {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  const seconds = Math.round((d.getTime() - now) / 1000);
  const rtf = new Intl.RelativeTimeFormat(i18n.locale, { numeric: 'auto' });
  for (const [unit, size] of UNITS) {
    if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
  }
  return rtf.format(seconds, 'second');
}

export function formatBytes(bytes: number | undefined) {
  if (bytes === undefined) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
