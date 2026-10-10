import { reactConfig } from '@app/eslint-config/react';

export default [
  {
    ignores: [
      'src/routeTree.gen.ts',
      'src/api/schema.d.ts',
      'dist/**',
      'src/locales/**/*.js',
      'src/locales/**/*.mjs',
    ],
  },
  ...reactConfig,
  {
    languageOptions: {
      parserOptions: {
        projectService: {
          allowDefaultProject: ['*.config.js', 'eslint.config.js', 'scripts/*.mjs'],
        },
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    // Layering: ui/ and lib/ know nothing about features; features do not import each other;
    // routes compose features. Violations fail lint instead of relying on convention.
    rules: {
      'import-x/no-restricted-paths': [
        'error',
        {
          basePath: './src',
          zones: [
            {
              target: './components/ui',
              from: './components',
              except: ['./ui'],
              message: 'ui/ must not depend on feature components.',
            },
            {
              target: './components/ui',
              from: './routes',
              message: 'ui/ must not depend on routes.',
            },
            {
              target: './components/ui',
              from: './api',
              message: 'ui/ must not depend on the api layer.',
            },
            {
              target: './lib',
              from: ['./components', './routes', './api'],
              except: ['../api/errors.ts', '../api/types.ts'],
              message: 'lib/ must stay independent of features.',
            },
            {
              target: './components/chat',
              from: './components',
              except: ['./ui', './chat'],
              message: 'Features share code through ui/, lib/ or api/, not each other.',
            },
            {
              target: './components/companies',
              from: './components',
              except: ['./ui', './companies'],
              message: 'Features share code through ui/, lib/ or api/, not each other.',
            },
            {
              target: './components/guidelines',
              from: './components',
              except: ['./ui', './guidelines', './companies'],
              message: 'Features share code through ui/, lib/ or api/, not each other.',
            },
            {
              target: './components/history',
              from: './components',
              except: ['./ui', './history', './chat'],
              message: 'Features share code through ui/, lib/ or api/, not each other.',
            },
            {
              target: './components/feedback',
              from: './components',
              except: ['./ui', './feedback'],
              message: 'Features share code through ui/, lib/ or api/, not each other.',
            },
            {
              target: './api',
              from: ['./components', './routes'],
              message: 'The api layer must not import UI.',
            },
          ],
        },
      ],
      // TanStack Router's beforeLoad idiom is `throw redirect(...)` / `throw notFound()`.
      '@typescript-eslint/only-throw-error': [
        'error',
        {
          allow: [
            { from: 'package', package: '@tanstack/router-core', name: 'Redirect' },
            { from: 'package', package: '@tanstack/router-core', name: 'NotFoundError' },
          ],
        },
      ],
    },
  },
  {
    files: ['*.config.{js,ts}', 'eslint.config.js'],
    ...{ rules: { 'import-x/no-unresolved': 'off' } },
  },
];
