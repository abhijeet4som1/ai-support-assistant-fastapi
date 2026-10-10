import { Trans } from '@lingui/react/macro';
import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, useNavigate } from '@tanstack/react-router';

import { companiesQuery } from '@/api/companies';
import { useConversationsInfinite } from '@/api/conversations';
import { toUiError } from '@/api/errors';
import { ConversationTable } from '@/components/history/conversation-table';
import { HistoryFilters, type HistoryFilterValues } from '@/components/history/history-filters';
import { Alert } from '@/components/ui/alert';
import { PageHeader } from '@/components/ui/page-header';
import { Spinner } from '@/components/ui/spinner';
import { isCoverage } from '@/lib/coverage';

export const Route = createFileRoute('/_authenticated/history/')({
  validateSearch: (search: Record<string, unknown>): HistoryFilterValues => ({
    ...(typeof search.companyId === 'string' ? { companyId: search.companyId } : {}),
    ...(isCoverage(search.coverage) ? { coverage: search.coverage } : {}),
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(companiesQuery()),
  component: HistoryPage,
});

function HistoryPage() {
  const filters = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const { data: companiesData } = useSuspenseQuery(companiesQuery());
  const companies = companiesData.items;
  const conversations = useConversationsInfinite({ ...filters, limit: 20 });
  const items = conversations.data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <>
      <PageHeader
        title={<Trans>Chat History</Trans>}
        description={
          <Trans>
            Browse previous conversations and see why the assistant answered the way it did.
          </Trans>
        }
      />
      <div className="bg-surface mb-4 rounded-lg border p-4 shadow-sm">
        <HistoryFilters
          companies={companies}
          value={filters}
          onChange={(next) => void navigate({ search: next })}
        />
      </div>
      {conversations.isPending ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : conversations.isError ? (
        <Alert variant="danger">{toUiError(conversations.error).message}</Alert>
      ) : (
        <ConversationTable
          conversations={items}
          hasMore={conversations.hasNextPage}
          loadingMore={conversations.isFetchingNextPage}
          onLoadMore={() => void conversations.fetchNextPage()}
        />
      )}
    </>
  );
}
