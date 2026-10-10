import { Trans } from '@lingui/react/macro';
import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, Link } from '@tanstack/react-router';
import { ArrowLeft, MessageSquare } from 'lucide-react';

import { conversationQuery, useLoadOlderMessages } from '@/api/conversations';
import { CoverageBadge } from '@/components/chat/coverage-badge';
import { MessageThread } from '@/components/chat/message-thread';
import { WhyPanel } from '@/components/history/why-panel';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/ui/page-header';
import { formatDateTime } from '@/lib/format';

export const Route = createFileRoute('/_authenticated/history/$conversationId')({
  loader: ({ context, params }) =>
    context.queryClient.ensureQueryData(conversationQuery(params.conversationId)),
  component: ConversationDetailPage,
});

function ConversationDetailPage() {
  const { conversationId } = Route.useParams();
  const { data } = useSuspenseQuery(conversationQuery(conversationId));
  const { summary, messages } = data.conversation;
  const loadOlder = useLoadOlderMessages(conversationId);
  return (
    <>
      <div className="mb-4">
        <Button asChild variant="ghost" size="sm">
          <Link to="/history">
            <ArrowLeft aria-hidden />
            <Trans>All conversations</Trans>
          </Link>
        </Button>
      </div>
      <PageHeader
        title={summary.title || <Trans>New conversation</Trans>}
        description={
          <span className="flex flex-wrap items-center gap-2">
            <span>{summary.companyName}</span>
            <span>·</span>
            <span>
              <Trans>
                started by {summary.createdBy?.displayName} on {formatDateTime(summary.createdAt)}
              </Trans>
            </span>
            <CoverageBadge coverage={summary.lastCoverage} />
          </span>
        }
        actions={
          <Button asChild>
            <Link to="/chat" search={{ companyId: summary.companyId, conversationId: summary.id }}>
              <MessageSquare aria-hidden />
              <Trans>Continue in chat</Trans>
            </Link>
          </Button>
        }
      />
      <div className="bg-surface rounded-lg border p-4 shadow-sm">
        <MessageThread
          messages={messages}
          renderFeedback={(m) => <WhyPanel message={m} />}
          hasOlder={Boolean(data.olderCursor)}
          loadingOlder={loadOlder.isPending}
          onLoadOlder={() => {
            if (data.olderCursor) loadOlder.mutate(data.olderCursor);
          }}
        />
      </div>
    </>
  );
}
