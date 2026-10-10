import { Trans, useLingui } from '@lingui/react/macro';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';

import { toUiError } from '@/api/errors';
import { correctionsQuery, useUpdateCorrection } from '@/api/feedback';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Spinner } from '@/components/ui/spinner';

import { CorrectionsList } from './corrections-list';

export function CorrectionsSection({ companyId }: { companyId: string }) {
  const { t } = useLingui();
  const corrections = useQuery(correctionsQuery(companyId, true));
  const update = useUpdateCorrection(companyId);
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <Trans>Corrections from agents</Trans>
        </CardTitle>
        <CardDescription>
          <Trans>
            Golden examples collected from thumbs-down feedback. Active corrections are retrieved
            for similar customer messages; they are deactivated automatically when the guidelines
            are replaced.
          </Trans>
        </CardDescription>
      </CardHeader>
      <CardContent>
        {corrections.isPending ? (
          <Spinner />
        ) : (
          <CorrectionsList
            corrections={corrections.data?.items ?? []}
            busyId={update.variables?.correctionId}
            onToggle={(c, active) =>
              void update
                .mutateAsync({ correctionId: c.id, active })
                .then(() =>
                  toast.success(active ? t`Correction reactivated` : t`Correction deactivated`),
                )
                .catch((err: unknown) => toast.error(toUiError(err).message))
            }
          />
        )}
      </CardContent>
    </Card>
  );
}
