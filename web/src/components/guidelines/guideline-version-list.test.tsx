import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { type GuidelineVersionSummary } from '@/api/types';

import { GuidelineVersionList } from './guideline-version-list';

const v = (over: Partial<GuidelineVersionSummary>): GuidelineVersionSummary => ({
  id: 'v',
  companyId: 'c',
  filename: 'f.txt',
  contentType: 'text/plain',
  sizeBytes: 2048,
  status: 'ready',
  chunksTotal: 3,
  chunksEmbedded: 3,
  isActive: false,
  uploadedBy: { id: 'u', username: 'agent1', displayName: 'Agent1' },
  createdAt: '2026-09-13T09:00:00Z',
  updatedAt: '2026-09-13T09:00:00Z',
  ...over,
});

describe('GuidelineVersionList', () => {
  it('offers activation only for ready, non-active versions and retry for failed ones', async () => {
    const onActivate = vi.fn();
    const onRetry = vi.fn();
    render(
      <I18nProvider i18n={i18n}>
        <GuidelineVersionList
          versions={[
            v({ id: 'a', filename: 'active.txt', isActive: true }),
            v({ id: 'b', filename: 'old.txt' }),
            v({ id: 'c', filename: 'broken.txt', status: 'failed', error: 'quota exceeded' }),
            v({ id: 'd', filename: 'gone.txt', status: 'superseded' }),
          ]}
          onActivate={onActivate}
          onRetry={onRetry}
        />
      </I18nProvider>,
    );
    expect(screen.getAllByRole('button', { name: /make active/i })).toHaveLength(1);
    await userEvent.click(screen.getByRole('button', { name: /make active/i }));
    expect(onActivate).toHaveBeenCalledWith('b');
    await userEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledWith('c');
    expect(screen.getByText('quota exceeded')).toBeInTheDocument();
    expect(screen.getByText(/superseded/i)).toBeInTheDocument();
  });
});
