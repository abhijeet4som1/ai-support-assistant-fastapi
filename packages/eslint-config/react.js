import jsxA11y from 'eslint-plugin-jsx-a11y';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import { createTypeScriptImportResolver } from 'eslint-import-resolver-typescript';
import globals from 'globals';

import { base } from './base.js';

/** @type {import('eslint').Linter.Config[]} */
export const reactConfig = [
  ...base,
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      'jsx-a11y': jsxA11y,
    },
    languageOptions: {
      globals: { ...globals.browser },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    settings: {
      react: { version: 'detect' },
      'import-x/resolver-next': [createTypeScriptImportResolver({ alwaysTryTypes: true })],
    },
    rules: {
      ...react.configs.flat.recommended.rules,
      ...react.configs.flat['jsx-runtime'].rules,
      ...reactHooks.configs['recommended-latest'].rules,
      ...jsxA11y.flatConfigs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      // Design-system rules: no inline styles, no template-literal class building.
      'react/forbid-dom-props': [
        'error',
        {
          forbid: [
            {
              propName: 'style',
              message: 'Use Tailwind classes / design tokens instead of inline styles.',
            },
          ],
        },
      ],
      'react/forbid-component-props': [
        'error',
        {
          forbid: [
            {
              propName: 'style',
              message: 'Use Tailwind classes / design tokens instead of inline styles.',
            },
          ],
        },
      ],
      'no-restricted-syntax': [
        'error',
        {
          selector:
            'JSXAttribute[name.name="className"] > JSXExpressionContainer > TemplateLiteral',
          message:
            'Do not build class names with template literals; use cn() and cva variants (static classes only).',
        },
      ],
      'react/prop-types': 'off',
      'react/self-closing-comp': 'error',
      'react/jsx-no-useless-fragment': 'error',
    },
  },
];
