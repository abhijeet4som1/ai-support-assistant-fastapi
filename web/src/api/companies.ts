import { useMutation, useQueryClient } from '@tanstack/react-query';

import { $api, apiClient } from './client';
import { type Company } from './types';

export const companyKeys = {
  list: ['get', '/api/companies'] as const,
  detail: ['get', '/api/companies/{companyId}'] as const,
};

/** All companies with guideline status summaries: `data.items`. */
export const companiesQuery = () => $api.queryOptions('get', '/api/companies');

/** One company: `data.company`. */
export const companyQuery = (companyId: string) =>
  $api.queryOptions('get', '/api/companies/{companyId}', { params: { path: { companyId } } });

function useCompanyCacheWriter() {
  const qc = useQueryClient();
  return (company: Company) => {
    qc.setQueryData(companyQuery(company.id).queryKey, { company });
    void qc.invalidateQueries({ queryKey: companyKeys.list });
  };
}

export function useCreateCompany() {
  const write = useCompanyCacheWriter();
  return useMutation({
    mutationFn: async (input: { name: string; description?: string }) =>
      (await apiClient.POST('/api/companies', { body: input })).data!.company,
    onSuccess: write,
  });
}

export function useUpdateCompany() {
  const write = useCompanyCacheWriter();
  return useMutation({
    mutationFn: async (input: { companyId: string; name?: string; description?: string }) =>
      (
        await apiClient.PATCH('/api/companies/{companyId}', {
          params: { path: { companyId: input.companyId } },
          body: { name: input.name, description: input.description },
        })
      ).data!.company,
    onSuccess: write,
  });
}
