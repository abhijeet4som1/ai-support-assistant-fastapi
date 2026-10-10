import { Trans } from '@lingui/react/macro';
import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, Link } from '@tanstack/react-router';
import { ArrowLeft, MessageSquare, Pencil } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import { companyQuery, useUpdateCompany } from '@/api/companies';
import { isProcessing } from '@/api/guidelines';
import { CompanyForm } from '@/components/companies/company-form';
import { GuidelineStatusBadge } from '@/components/companies/guideline-status-badge';
import { CorrectionsSection } from '@/components/feedback/corrections-section';
import { GuidelineSection } from '@/components/guidelines/guideline-section';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/ui/page-header';

export const Route = createFileRoute('/_authenticated/companies/$companyId')({
  loader: ({ context, params }) =>
    context.queryClient.ensureQueryData(companyQuery(params.companyId)),
  component: CompanyPage,
});

function CompanyPage() {
  const { companyId } = Route.useParams();
  const { data } = useSuspenseQuery({
    ...companyQuery(companyId),
    // Keep the header badge fresh while an upload is being processed.
    refetchInterval: (query) =>
      isProcessing(query.state.data?.company.latestGuidelines?.status) ? 2000 : false,
  });
  const company = data.company;
  const update = useUpdateCompany();
  const [editing, setEditing] = useState(false);

  return (
    <>
      <div className="mb-4">
        <Button asChild variant="ghost" size="sm">
          <Link to="/companies">
            <ArrowLeft aria-hidden />
            <Trans>All companies</Trans>
          </Link>
        </Button>
      </div>
      <PageHeader
        title={company.name}
        description={
          <span className="flex flex-wrap items-center gap-2">
            <GuidelineStatusBadge
              active={company.activeGuidelines}
              latest={company.latestGuidelines}
            />
            <span className="inline-flex items-center gap-1">
              <MessageSquare className="size-4" aria-hidden />
              <Trans>{company.conversationCount ?? 0} conversations</Trans>
            </span>
          </span>
        }
        actions={
          <>
            <Button variant="outline" onClick={() => setEditing((v) => !v)}>
              <Pencil aria-hidden />
              <Trans>Edit</Trans>
            </Button>
            <Button asChild disabled={!company.activeGuidelines}>
              <Link to="/chat" search={{ companyId: company.id }}>
                <MessageSquare aria-hidden />
                <Trans>Open chat</Trans>
              </Link>
            </Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {editing ? (
            <Card>
              <CardHeader>
                <CardTitle>
                  <Trans>Edit company</Trans>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CompanyForm
                  defaultValues={{
                    name: company.name ?? '',
                    description: company.description ?? '',
                  }}
                  submitLabel={<Trans>Save changes</Trans>}
                  pending={update.isPending}
                  onCancel={() => setEditing(false)}
                  onSubmit={async (values) => {
                    await update.mutateAsync({
                      companyId,
                      name: values.name,
                      description: values.description,
                    });
                    toast.success(<Trans>Company updated</Trans>);
                    setEditing(false);
                  }}
                />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>
                  <Trans>About</Trans>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">
                  {company.description ? company.description : <Trans>No description</Trans>}
                </p>
              </CardContent>
            </Card>
          )}

          <GuidelineSection company={company} />
          <CorrectionsSection companyId={companyId} />
        </div>
      </div>
    </>
  );
}
