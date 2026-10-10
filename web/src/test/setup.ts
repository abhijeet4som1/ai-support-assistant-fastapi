import { Blob as NodeBlob } from 'node:buffer';

import '@testing-library/jest-dom/vitest';
import { i18n } from '@lingui/core';

import { messages } from '@/locales/en/messages.po';

i18n.load('en', messages);
i18n.activate('en');

// jsdom does not implement scrolling; TanStack Router and the chat thread call these.
window.scrollTo = () => undefined;
Element.prototype.scrollIntoView = () => undefined;

// jsdom's Blob is a different class from Node's; fetch/Request (Node) would stringify it.
// Using Node's Blob for `new Blob(...)` mirrors browser behaviour, where both are the same class.
// Assigned directly (not vi.stubGlobal) so tests calling vi.unstubAllGlobals() keep it.
Object.defineProperty(globalThis, 'Blob', { value: NodeBlob, configurable: true, writable: true });
