import { zodResolver } from '@hookform/resolvers/zod';
import { Trans, useLingui } from '@lingui/react/macro';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { toUiError } from '@/api/errors';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { FormField } from '@/components/ui/form-field';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { applyServerFieldErrors, fieldProps } from '@/lib/form';

export interface CompanyFormValues {
  name: string;
  description: string;
}

export interface CompanyFormProps {
  defaultValues?: Partial<CompanyFormValues>;
  submitLabel: React.ReactNode;
  pending?: boolean;
  onSubmit: (values: CompanyFormValues) => Promise<unknown>;
  onCancel?: () => void;
}

export function CompanyForm({
  defaultValues,
  submitLabel,
  pending,
  onSubmit,
  onCancel,
}: CompanyFormProps) {
  const { t } = useLingui();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<CompanyFormValues>({
    resolver: zodResolver(
      z.object({
        name: z
          .string()
          .trim()
          .min(1, t`Enter a company name`)
          .max(200, t`Keep the name under 200 characters`),
        description: z
          .string()
          .trim()
          .max(1000, t`Keep the description under 1000 characters`),
      }),
    ),
    defaultValues: {
      name: defaultValues?.name ?? '',
      description: defaultValues?.description ?? '',
    },
  });

  const submit = async (values: CompanyFormValues) => {
    setFormError(null);
    try {
      await onSubmit(values);
    } catch (err) {
      const ui = toUiError(err);
      if (applyServerFieldErrors(ui, setError, ['name', 'description'])) return;
      if (ui.kind === 'conflict') {
        setError('name', { type: 'server', message: ui.message });
        return;
      }
      setFormError(
        ui.kind === 'network'
          ? t`Cannot reach the server. Check your connection and try again.`
          : ui.message,
      );
    }
  };

  return (
    <form noValidate className="space-y-5" onSubmit={(e) => void handleSubmit(submit)(e)}>
      {formError ? <Alert variant="danger">{formError}</Alert> : null}
      <FormField
        htmlFor="company-name"
        label={<Trans>Company name</Trans>}
        error={errors.name?.message}
      >
        <Input
          {...register('name')}
          {...fieldProps('company-name', errors.name?.message)}
          placeholder={t`e.g. Bookshop`}
        />
      </FormField>
      <FormField
        htmlFor="company-description"
        label={<Trans>Description</Trans>}
        hint={<Trans>Optional. Shown in the company list.</Trans>}
        error={errors.description?.message}
      >
        <Textarea
          {...register('description')}
          {...fieldProps('company-description', errors.description?.message)}
          rows={3}
        />
      </FormField>
      <div className="flex justify-end gap-2">
        {onCancel ? (
          <Button type="button" variant="outline" onClick={onCancel}>
            <Trans>Cancel</Trans>
          </Button>
        ) : null}
        <Button type="submit" loading={pending}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
