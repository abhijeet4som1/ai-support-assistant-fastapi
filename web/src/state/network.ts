import { atom } from 'jotai';

import { appStore } from './store';

/** Set by the query/mutation caches when the api cannot be reached; cleared on the next success. */
export const apiUnreachableAtom = atom(false);
/** Mirrors navigator.onLine (updated by online/offline events in main.tsx). */
export const browserOnlineAtom = atom(typeof navigator === 'undefined' ? true : navigator.onLine);

export const networkProblemAtom = atom((get) => get(apiUnreachableAtom) || !get(browserOnlineAtom));

export const setApiUnreachable = (value: boolean) => {
  if (appStore.get(apiUnreachableAtom) !== value) appStore.set(apiUnreachableAtom, value);
};

export function watchBrowserOnline() {
  const update = () => appStore.set(browserOnlineAtom, navigator.onLine);
  window.addEventListener('online', update);
  window.addEventListener('offline', update);
  return () => {
    window.removeEventListener('online', update);
    window.removeEventListener('offline', update);
  };
}
