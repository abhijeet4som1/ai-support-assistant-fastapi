import { createTypeScriptImportResolver } from 'eslint-import-resolver-typescript';
import globals from 'globals';

import { base } from './base.js';

/** @type {import('eslint').Linter.Config[]} */
export const node = [
  ...base,
  {
    languageOptions: { globals: { ...globals.node } },
    settings: {
      'import-x/resolver-next': [createTypeScriptImportResolver({ alwaysTryTypes: true })],
    },
  },
];
