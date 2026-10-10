import { Trans } from '@lingui/react/macro';
import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, Link } from '@tanstack/react-router';
import { Plus } from 'lucide-react';

import { companiesQuery } from '@/api/companies';
import { isProcessing } from '@/api/guidelines';
import { CompanyList } from '@/components/companies/company-list';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/ui/page-header';

export const Route = createFileRoute('/_authenticated/companies/')({
  loader: ({ context }) => context.queryClient.ensureQueryData(companiesQuery()),
  component: CompaniesPage,
});

function CompaniesPage() {
  const { data } = useSuspenseQuery({
    ...companiesQuery(),
    refetchInterval: (query) =>
      query.state.data?.items.some((c) => isProcessing(c.latestGuidelines?.status)) ? 2000 : false,
  });
  return (
    <>
      <PageHeader
        title={<Trans>Companies</Trans>}
        description={<Trans>Manage companies and their support guidelines.</Trans>}
        actions={
          <Button asChild>
            <Link to="/companies/new">
              <Plus aria-hidden />
              <Trans>Add company</Trans>
            </Link>
          </Button>
        }
      />
      <CompanyList companies={data.items} />
    </>
  );
}
