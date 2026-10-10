import { zodResolver } from '@hookform/resolvers/zod';
import { Trans, useLingui } from '@lingui/react/macro';
import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiClient } from '@/api/client';
import { toUiError } from '@/api/errors';
import { setTokens, setUser, tokensFromApi } from '@/auth/atoms';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { FormField } from '@/components/ui/form-field';
import { Input } from '@/components/ui/input';
import { fieldProps } from '@/lib/form';

interface FormValues {
  username: string;
  password: string;
}

export function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const { t } = useLingui();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(
      z.object({
        username: z
          .string()
          .trim()
          .min(1, t`Enter your username`),
        password: z.string().min(1, t`Enter your password`),
      }),
    ),
    defaultValues: { username: '', password: '' },
  });

  const login = useMutation({
    mutationFn: async (values: FormValues) =>
      (await apiClient.POST('/api/auth/login', { body: values })).data!,
    onSuccess: (out) => {
      setTokens(tokensFromApi(out.tokens));
      setUser(out.user);
      onSuccess();
    },
    onError: (err) => {
      const ui = toUiError(err);
      switch (ui.kind) {
        case 'validation':
          for (const [name, message] of Object.entries(ui.fields)) {
            if (name === 'username' || name === 'password')
              setError(name, { type: 'server', message });
          }
          if (Object.keys(ui.fields).length === 0) setFormError(ui.message);
          break;
        case 'unauthorized':
          setFormError(t`Invalid username or password.`);
          break;
        case 'network':
          setFormError(t`Cannot reach the server. Check your connection and try again.`);
          break;
        default:
          setFormError(ui.message || t`Login failed. Please try again.`);
      }
    },
  });

  return (
    <form
      noValidate
      className="space-y-4"
      onSubmit={(e) => {
        setFormError(null);
        void handleSubmit((values) => login.mutate(values))(e);
      }}
    >
      {formError ? <Alert variant="danger">{formError}</Alert> : null}
      <FormField
        htmlFor="username"
        label={<Trans>Username</Trans>}
        error={errors.username?.message}
      >
        <Input
          {...register('username')}
          {...fieldProps('username', errors.username?.message)}
          autoComplete="username"
        />
      </FormField>
      <FormField
        htmlFor="password"
        label={<Trans>Password</Trans>}
        error={errors.password?.message}
      >
        <Input
          {...register('password')}
          {...fieldProps('password', errors.password?.message)}
          type="password"
          autoComplete="current-password"
        />
      </FormField>
      <Button type="submit" className="w-full" loading={login.isPending}>
        <Trans>Log in</Trans>
      </Button>
    </form>
  );
}
