import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { render, screen } from '@testing-library/react';

import { type Message } from '@/api/types';

import { WhyPanel } from './why-panel';

const base: Message = {
  id: 'm',
  conversationId: 'c',
  role: 'assistant',
  content: '',
  status: 'ok',
  model: 'gemini-3.8-flash',
  promptTokens: 1200,
  thinkingTokens: 450,
  completionTokens: 300,
  totalTokens: 1950,
  latencyMs: 2500,
  guidelineVersionId: 'abcdef12-3456',
  createdBy: { id: 'u', username: 'a', displayName: 'A' },
  createdAt: new Date().toISOString(),
  retrieval: [{ chunkId: 'k1', title: 'Shipping Issues', score: 0.82 }],
  correctionsUsed: [{ correctionId: 'corr-1', score: 0.71 }],
};

describe('WhyPanel', () => {
  it('lists retrieved sections with scores, corrections and model stats', () => {
    render(
      <I18nProvider i18n={i18n}>
        <WhyPanel message={base} />
      </I18nProvider>,
    );
    expect(screen.getByText('Shipping Issues')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
    expect(screen.getByText('corr-1')).toBeInTheDocument();
    expect(screen.getByText(/1200 prompt tokens/)).toBeInTheDocument();
    expect(screen.getByText(/450 thinking tokens/)).toBeInTheDocument();
    expect(screen.getByText(/300 output tokens/)).toBeInTheDocument();
    expect(screen.getByText(/1950 total tokens/)).toBeInTheDocument();
    expect(screen.getByText('2.5 s')).toBeInTheDocument();
  });

  it('explains an empty retrieval', () => {
    render(
      <I18nProvider i18n={i18n}>
        <WhyPanel message={{ ...base, retrieval: [], correctionsUsed: [] }} />
      </I18nProvider>,
    );
    expect(screen.getByText(/none above the relevance threshold/i)).toBeInTheDocument();
  });
});
