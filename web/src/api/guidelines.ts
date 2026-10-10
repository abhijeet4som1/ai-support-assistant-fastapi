import { useMutation, useQueryClient } from '@tanstack/react-query';

import { fileToBytes } from '@/lib/files';

import { $api, apiClient } from './client';
import { companyKeys, companyQuery } from './companies';
import { type GuidelineVersionSummary } from './types';

export const PROCESSING_STATUSES = new Set(['queued', 'parsing', 'chunking', 'embedding']);
export const isProcessing = (status?: string) => PROCESSING_STATUSES.has(status ?? '');
export const POLL_INTERVAL_MS = 2000;

/** One version with progress: `data.version`. Polls every 2 s while it is being processed. */
export const guidelineVersionQuery = (versionId: string) =>
  $api.queryOptions(
    'get',
    '/api/guideline-versions/{versionId}',
    { params: { path: { versionId } } },
    {
      refetchInterval: (query) =>
        isProcessing(query.state.data?.version.status) ? POLL_INTERVAL_MS : false,
    },
  );

/** Upload history of a company, newest first: `data.items`. */
export const guidelineVersionsQuery = (companyId: string) =>
  $api.queryOptions(
    'get',
    '/api/companies/{companyId}/guidelines/versions',
    { params: { path: { companyId } } },
    {
      refetchInterval: (query) =>
        query.state.data?.items.some((v) => isProcessing(v.status)) ? POLL_INTERVAL_MS : false,
    },
  );

/**
 * Active guidelines with text and chunks. 409 GuidelinesNotReady when none is ready.
 * `activeVersionId` is part of the cache key (openapi-react-query allows extra init keys for
 * that), so the viewer refetches as soon as the polled company data reports a new active version.
 */
export const activeGuidelinesQuery = (companyId: string, activeVersionId?: string) =>
  $api.queryOptions(
    'get',
    '/api/companies/{companyId}/guidelines',
    { params: { path: { companyId } }, activeVersionId },
    { retry: false },
  );

export interface UploadArgs {
  companyId: string;
  file: File;
  /** Latest version id the user saw; omit to force-replace after a conflict. */
  expectedVersionId?: string;
}

function useInvalidateGuidelines() {
  const qc = useQueryClient();
  return (companyId: string, version?: GuidelineVersionSummary) => {
    if (version) qc.setQueryData(guidelineVersionQuery(version.id).queryKey, { version });
    void qc.invalidateQueries({ queryKey: guidelineVersionsQuery(companyId).queryKey });
    void qc.invalidateQueries({ queryKey: ['get', '/api/companies/{companyId}/guidelines'] });
    void qc.invalidateQueries({ queryKey: companyQuery(companyId).queryKey });
    void qc.invalidateQueries({ queryKey: companyKeys.list });
  };
}

export function useUploadGuidelines() {
  const invalidate = useInvalidateGuidelines();
  return useMutation({
    mutationFn: async ({ companyId, file, expectedVersionId }: UploadArgs) => {
      const bytes = await fileToBytes(file);
      const header = {
        'X-Filename': file.name,
        ...(file.type ? { 'X-File-Content-Type': file.type } : {}),
        ...(expectedVersionId ? { 'X-Expected-Version': expectedVersionId } : {}),
      };
      const res = await apiClient.PUT('/api/companies/{companyId}/guidelines', {
        params: { path: { companyId }, header },
        // Binary payloads are typed as Blob (see scripts/gen-api-types.mjs); sent as-is.
        body: new Blob([bytes]),
        bodySerializer: (b) => b,
        headers: { 'content-type': 'application/octet-stream' },
      });
      return res.data!.version;
    },
    onSuccess: (version, { companyId }) => invalidate(companyId, version),
  });
}

export function useRetryGuidelineVersion(companyId: string) {
  const invalidate = useInvalidateGuidelines();
  return useMutation({
    mutationFn: async (versionId: string) =>
      (
        await apiClient.POST('/api/guideline-versions/{versionId}/retry', {
          params: { path: { versionId } },
        })
      ).data!.version,
    onSuccess: (version) => invalidate(companyId, version),
  });
}

export function useActivateGuidelineVersion(companyId: string) {
  const invalidate = useInvalidateGuidelines();
  return useMutation({
    mutationFn: async (versionId: string) =>
      (
        await apiClient.POST('/api/guideline-versions/{versionId}/activate', {
          params: { path: { versionId } },
        })
      ).data!.version,
    onSuccess: (version) => invalidate(companyId, version),
  });
}
