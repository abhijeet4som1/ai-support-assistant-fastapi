import { Trans } from '@lingui/react/macro';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { toast } from 'sonner';

import { useCreateCompany } from '@/api/companies';
import { CompanyForm } from '@/components/companies/company-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/ui/page-header';

export const Route = createFileRoute('/_authenticated/companies/new')({
  component: NewCompanyPage,
});

function NewCompanyPage() {
  const navigate = useNavigate();
  const create = useCreateCompany();
  return (
    <>
      <PageHeader
        title={<Trans>Add company</Trans>}
        description={
          <Trans>Create the company first; you upload its guidelines on the next screen.</Trans>
        }
      />
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>
            <Trans>Company details</Trans>
          </CardTitle>
          <CardDescription>
            <Trans>The name must be unique across companies.</Trans>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CompanyForm
            submitLabel={<Trans>Create company</Trans>}
            pending={create.isPending}
            onCancel={() => void navigate({ to: '/companies' })}
            onSubmit={async (values) => {
              const company = await create.mutateAsync({
                name: values.name,
                description: values.description || undefined,
              });
              toast.success(<Trans>Company created</Trans>);
              await navigate({ to: '/companies/$companyId', params: { companyId: company.id } });
            }}
          />
        </CardContent>
      </Card>
    </>
  );
}
