import { Trans, useLingui } from '@lingui/react/macro';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { toast } from 'sonner';

import { companyKeys, companyQuery } from '@/api/companies';
import { toUiError } from '@/api/errors';
import {
  activeGuidelinesQuery,
  guidelineVersionsQuery,
  isProcessing,
  useActivateGuidelineVersion,
  useRetryGuidelineVersion,
} from '@/api/guidelines';
import { type Company } from '@/api/types';
import { Alert } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Spinner } from '@/components/ui/spinner';

import { GuidelineProgress } from './guideline-progress';
import { GuidelineUpload } from './guideline-upload';
import { GuidelineVersionList } from './guideline-version-list';
import { GuidelineViewer } from './guideline-viewer';

/** Everything guideline-related on the company page: upload, progress, active content, history. */
export function GuidelineSection({ company }: { company: Company }) {
  const { t } = useLingui();
  const companyId = company.id;
  const versions = useQuery(guidelineVersionsQuery(companyId));
  const active = useQuery({
    ...activeGuidelinesQuery(companyId),
    enabled: Boolean(company.activeGuidelines),
  });
  const retry = useRetryGuidelineVersion(companyId);
  const activate = useActivateGuidelineVersion(companyId);

  const latest = versions.data?.items[0] ?? company.latestGuidelines;
  const processing = latest && isProcessing(latest.status);

  // When the latest version stops processing, refresh everything derived from it.
  const qc = useQueryClient();
  const wasProcessing = useRef(false);
  useEffect(() => {
    if (wasProcessing.current && !processing) {
      void qc.invalidateQueries({ queryKey: companyQuery(companyId).queryKey });
      void qc.invalidateQueries({ queryKey: companyKeys.list });
      void qc.invalidateQueries({ queryKey: ['get', '/api/companies/{companyId}/guidelines'] });
    }
    wasProcessing.current = Boolean(processing);
  }, [processing, qc, companyId]);
  const failedLatest = latest?.status === 'failed';

  const run = async (action: Promise<unknown>, successMessage: string) => {
    try {
      await action;
      toast.success(successMessage);
    } catch (err) {
      toast.error(toUiError(err).message);
    }
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>
            <Trans>Guidelines</Trans>
          </CardTitle>
          <CardDescription>
            <Trans>
              The support guidelines the assistant follows for this company. Uploading a new file
              replaces the current one once processing finishes.
            </Trans>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {latest && (processing || failedLatest) ? (
            <div className="space-y-2">
              {processing && company.activeGuidelines ? (
                <Alert variant="info">
                  <Trans>
                    New guidelines are being processed. Chat keeps using the current version until
                    they are ready.
                  </Trans>
                </Alert>
              ) : null}
              <GuidelineProgress
                version={latest}
                retrying={retry.isPending}
                onRetry={() => void run(retry.mutateAsync(latest.id), t`Retry queued`)}
              />
            </div>
          ) : null}

          <GuidelineUpload companyId={companyId} latestVersion={latest} />

          {company.activeGuidelines ? (
            active.isPending ? (
              <Spinner />
            ) : active.data ? (
              <GuidelineViewer
                version={active.data.version}
                text={active.data.text ?? ''}
                chunks={active.data.chunks ?? []}
              />
            ) : null
          ) : !latest ? (
            <Alert variant="warning">
              <Trans>
                No guidelines yet. Chat is disabled for this company until a file has been
                processed.
              </Trans>
            </Alert>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            <Trans>Upload history</Trans>
          </CardTitle>
          <CardDescription>
            <Trans>Any processed version can be made active again.</Trans>
          </CardDescription>
        </CardHeader>
        <CardContent>
          {versions.isPending ? (
            <Spinner />
          ) : (
            <GuidelineVersionList
              versions={versions.data?.items ?? []}
              busyId={activate.variables ?? retry.variables}
              onActivate={(id) => void run(activate.mutateAsync(id), t`Version activated`)}
              onRetry={(id) => void run(retry.mutateAsync(id), t`Retry queued`)}
            />
          )}
        </CardContent>
      </Card>
    </>
  );
}
