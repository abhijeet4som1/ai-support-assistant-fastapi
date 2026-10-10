import { createStore } from 'jotai';

/**
 * The single Jotai store. Components read it through <Provider store={appStore}>; code that runs
 * outside React (router guards, fetch middleware) uses appStore.get / appStore.set directly.
 */
export const appStore = createStore();
