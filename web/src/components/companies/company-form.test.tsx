import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ApiError } from '@/api/api-error';

import { CompanyForm } from './company-form';

const renderForm = (onSubmit: (v: unknown) => Promise<unknown>) =>
  render(
    <I18nProvider i18n={i18n}>
      <CompanyForm submitLabel="Save" onSubmit={onSubmit} />
    </I18nProvider>,
  );

describe('CompanyForm', () => {
  it('requires a name before submitting', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    renderForm(onSubmit);
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/enter a company name/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('shows a conflict on the name field', async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      new ApiError({
        status: 409,
        type: 'ConflictError',
        body: { message: 'A company named "X" already exists' },
      }),
    );
    renderForm(onSubmit);
    await userEvent.type(screen.getByLabelText(/company name/i), 'X');
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/already exists/);
    expect(screen.getByLabelText(/company name/i)).toHaveAttribute('aria-invalid', 'true');
  });

  it('maps server validation onto fields', async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      new ApiError({
        status: 400,
        type: 'ValidationException',
        body: { message: 'invalid', fieldList: [{ path: '/description', message: 'too long' }] },
      }),
    );
    renderForm(onSubmit);
    await userEvent.type(screen.getByLabelText(/company name/i), 'X');
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByText('too long')).toBeInTheDocument();
  });

  it('submits trimmed values', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    renderForm(onSubmit);
    await userEvent.type(screen.getByLabelText(/company name/i), '  Bookshop ');
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(onSubmit).toHaveBeenCalledWith({ name: 'Bookshop', description: '' });
  });
});
