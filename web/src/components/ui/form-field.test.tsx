import { render, screen } from '@testing-library/react';

import { fieldProps } from '@/lib/form';

import { FormField } from './form-field';
import { Input } from './input';

describe('FormField', () => {
  it('links label, control and error for assistive tech', () => {
    render(
      <FormField htmlFor="username" label="Username" error="Required">
        <Input {...fieldProps('username', 'Required')} />
      </FormField>,
    );
    const input = screen.getByLabelText('Username');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby', 'username-error');
    expect(screen.getByRole('alert')).toHaveTextContent('Required');
  });

  it('shows the hint only while there is no error', () => {
    const { rerender } = render(
      <FormField htmlFor="f" label="F" hint="Be nice">
        <Input id="f" />
      </FormField>,
    );
    expect(screen.getByText('Be nice')).toBeInTheDocument();
    rerender(
      <FormField htmlFor="f" label="F" hint="Be nice" error="Nope">
        <Input id="f" />
      </FormField>,
    );
    expect(screen.queryByText('Be nice')).not.toBeInTheDocument();
  });
});
