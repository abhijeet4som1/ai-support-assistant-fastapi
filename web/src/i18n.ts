import { i18n, type Messages } from '@lingui/core';

import { oneOf } from '@/lib/guards';

export const LOCALES = ['en', 'de'] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = 'en';
export const isLocale = oneOf(LOCALES);
const STORAGE_KEY = 'locale';

/** Static map so each catalog import is statically analysable and typed by the *.po declaration. */
const catalogs: Record<Locale, () => Promise<{ messages: Messages }>> = {
  en: () => import('./locales/en/messages.po'),
  de: () => import('./locales/de/messages.po'),
};

export function detectLocale(): Locale {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (isLocale(stored)) return stored;
  } catch {
    /* storage unavailable */
  }
  const nav = navigator.language.slice(0, 2);
  return isLocale(nav) ? nav : DEFAULT_LOCALE;
}

export async function activateLocale(locale: Locale) {
  const { messages } = await catalogs[locale]();
  i18n.load(locale, messages);
  i18n.activate(locale);
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    /* storage unavailable */
  }
}
