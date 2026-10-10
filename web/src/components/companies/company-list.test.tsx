import { screen } from '@testing-library/react';

import { type Company, type GuidelineVersionSummary } from '@/api/types';
import { renderWithRouter } from '@/test/render-with-router';

import { CompanyList } from './company-list';

const base = {
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  conversationCount: 3,
};
const version = (status: GuidelineVersionSummary['status']): GuidelineVersionSummary => ({
  id: 'v1',
  companyId: 'c1',
  filename: 'g.txt',
  contentType: 'text/plain',
  sizeBytes: 10,
  status,
  chunksTotal: 10,
  chunksEmbedded: 5,
  isActive: status === 'ready',
  uploadedBy: { id: 'u', username: 'agent1', displayName: 'Agent1' },
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
});

describe('CompanyList', () => {
  it('renders an empty state', async () => {
    renderWithRouter(<CompanyList companies={[]} />);
    expect(await screen.findByText(/no companies yet/i)).toBeInTheDocument();
  });

  it('shows guideline status per company', async () => {
    const companies: Company[] = [
      { ...base, id: 'a', name: 'Alpha' },
      { ...base, id: 'b', name: 'Beta', latestGuidelines: version('embedding') },
      {
        ...base,
        id: 'c',
        name: 'Gamma',
        activeGuidelines: version('ready'),
        latestGuidelines: version('ready'),
      },
      { ...base, id: 'd', name: 'Delta', latestGuidelines: version('failed') },
    ];
    renderWithRouter(<CompanyList companies={companies} />);
    expect(await screen.findByText(/no guidelines yet/i)).toBeInTheDocument();
    expect(screen.getByText(/processing 50%/i)).toBeInTheDocument();
    expect(screen.getByText(/guidelines updated/i)).toBeInTheDocument();
    expect(screen.getByText(/processing failed/i)).toBeInTheDocument();
    expect(screen.getAllByRole('link')).toHaveLength(4);
  });
});
