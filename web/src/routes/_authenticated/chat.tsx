import { Trans, useLingui } from '@lingui/react/macro';
import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, Link, useNavigate } from '@tanstack/react-router';
import { useAtomValue } from 'jotai';
import { toast } from 'sonner';

import { companiesQuery } from '@/api/companies';
import {
  conversationQuery,
  useLoadOlderMessages,
  useConversationsInfinite,
  useCreateConversation,
  useSendMessage,
} from '@/api/conversations';
import { toUiError } from '@/api/errors';
import { isProcessing } from '@/api/guidelines';
import { type Message, type MessageKind } from '@/api/types';
import { userAtom } from '@/auth/atoms';
import { CompanyPicker } from '@/components/chat/company-picker';
import { Composer } from '@/components/chat/composer';
import { ConversationList } from '@/components/chat/conversation-list';
import { MessageThread } from '@/components/chat/message-thread';
import { FeedbackControls } from '@/components/feedback/feedback-controls';
import { Alert } from '@/components/ui/alert';
import { PageHeader } from '@/components/ui/page-header';
import { Spinner } from '@/components/ui/spinner';
import { formatRelative } from '@/lib/format';

export const Route = createFileRoute('/_authenticated/chat')({
  validateSearch: (
    search: Record<string, unknown>,
  ): { companyId?: string; conversationId?: string } => ({
    ...(typeof search.companyId === 'string' ? { companyId: search.companyId } : {}),
    ...(typeof search.conversationId === 'string' ? { conversationId: search.conversationId } : {}),
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(companiesQuery()),
  component: ChatPage,
});

function ChatPage() {
  const { t } = useLingui();
  const user = useAtomValue(userAtom);
  const { companyId, conversationId } = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const { data: companiesData } = useSuspenseQuery({
    ...companiesQuery(),
    // Keep the guideline notice fresh while a colleague's upload is being processed.
    refetchInterval: (query) =>
      query.state.data?.items.some((c) => isProcessing(c.latestGuidelines?.status)) ? 2000 : false,
  });
  const companies = companiesData.items;
  const company = companies.find((c) => c.id === companyId);

  const conversations = useConversationsInfinite(
    { companyId, limit: 20 },
    { enabled: Boolean(companyId) },
  );
  const conversation = useQuery({
    ...conversationQuery(conversationId ?? ''),
    enabled: Boolean(conversationId),
  });
  const create = useCreateConversation();
  const send = useSendMessage();
  const loadOlder = useLoadOlderMessages(conversationId ?? '');

  const setSearch = (next: { companyId?: string; conversationId?: string }) =>
    void navigate({ search: (prev) => ({ ...prev, ...next }), replace: false });

  const startConversation = async () => {
    if (!companyId) return;
    try {
      const created = await create.mutateAsync(companyId);
      setSearch({ companyId, conversationId: created.summary.id });
    } catch (err) {
      toast.error(toUiError(err).message);
    }
  };

  const sendMessage = async (kind: MessageKind, content: string) => {
    if (!conversationId) return;
    try {
      await send.mutateAsync({ conversationId, kind, content });
    } catch (err) {
      const ui = toUiError(err);
      toast.error(
        ui.kind === 'network' ? t`Cannot reach the server. Your message was not sent.` : ui.message,
      );
    }
  };

  const retry = (userMessage: Message) => {
    void sendMessage(
      userMessage.role === 'instruction' ? 'instruction' : 'customer',
      userMessage.content ?? '',
    );
  };

  const items = conversations.data?.pages.flatMap((p) => p.items) ?? [];

  // Show the agent's message immediately while the assistant is thinking. A retry re-sends a
  // message that is already in the thread, so no optimistic copy is added in that case.
  const serverMessages = conversation.data?.conversation.messages ?? [];
  const lastUser = [...serverMessages].reverse().find((m) => m.role !== 'assistant');
  const pendingVars = send.isPending ? send.variables : undefined;
  const isRetry =
    pendingVars && lastUser?.content === pendingVars.content && lastUser.role === pendingVars.kind;
  const optimistic: Message[] =
    pendingVars && !isRetry && user
      ? [
          {
            id: 'pending-user-message',
            conversationId: pendingVars.conversationId,
            role: pendingVars.kind,
            content: pendingVars.content,
            status: 'ok',
            createdBy: user,
            createdAt: new Date().toISOString(),
          },
        ]
      : [];
  const threadMessages = isRetry
    ? serverMessages.filter(
        (m) => !(m.role === 'assistant' && m.status === 'failed' && m === serverMessages.at(-1)),
      )
    : [...serverMessages, ...optimistic];

  return (
    <>
      <PageHeader
        title={<Trans>Support Chat</Trans>}
        description={
          <Trans>
            Paste a customer message and get a reply grounded in the guidelines of the company.
          </Trans>
        }
      />
      <div className="grid gap-6 lg:grid-cols-12">
        <aside className="space-y-4 lg:col-span-3">
          <div className="bg-surface rounded-lg border p-4 shadow-sm">
            <CompanyPicker
              companies={companies}
              value={companyId}
              onChange={(id) => setSearch({ companyId: id, conversationId: undefined })}
            />
          </div>
          {companyId ? (
            <div className="bg-surface rounded-lg border p-4 shadow-sm">
              {conversations.isPending ? (
                <Spinner />
              ) : (
                <ConversationList
                  conversations={items}
                  activeId={conversationId}
                  onSelect={(id) => setSearch({ companyId, conversationId: id })}
                  onNew={() => void startConversation()}
                  creating={create.isPending}
                  hasMore={conversations.hasNextPage}
                  onLoadMore={() => void conversations.fetchNextPage()}
                />
              )}
            </div>
          ) : null}
        </aside>

        <section className="bg-surface flex min-h-[600px] flex-col rounded-lg border shadow-sm lg:col-span-9">
          <header className="space-y-2 border-b px-4 py-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">
                {company?.name ?? t`No company selected`}
              </p>
              <p className="text-muted-foreground truncate text-xs">
                {conversation.data?.conversation.summary.title ||
                  (conversationId
                    ? t`New conversation`
                    : t`Pick a company and start a conversation`)}
              </p>
            </div>
            {company?.activeGuidelines ? (
              <p className="text-muted-foreground flex flex-wrap items-center gap-x-1 text-xs">
                <Trans>
                  Answers follow{' '}
                  <span className="text-foreground font-medium">
                    {company.activeGuidelines.filename}
                  </span>
                  , updated{' '}
                  {formatRelative(
                    company.activeGuidelines.readyAt ?? company.activeGuidelines.createdAt,
                  )}
                  .
                </Trans>
                <Link
                  to="/companies/$companyId"
                  params={{ companyId: company.id }}
                  className="text-primary underline"
                >
                  <Trans>View guidelines</Trans>
                </Link>
              </p>
            ) : null}
            {company && isProcessing(company.latestGuidelines?.status) ? (
              <Alert variant="info" className="py-2 text-xs">
                <Trans>
                  New guidelines are being processed. Answers keep using the current version until
                  they are ready.
                </Trans>
              </Alert>
            ) : null}
          </header>

          <div className="flex-1 overflow-y-auto p-4">
            {!companyId ? (
              <p className="text-muted-foreground py-16 text-center text-sm">
                <Trans>Select a company on the left to begin.</Trans>
              </p>
            ) : !conversationId ? (
              <p className="text-muted-foreground py-16 text-center text-sm">
                <Trans>Start a new conversation or pick a recent one.</Trans>
              </p>
            ) : conversation.isPending ? (
              <div className="flex justify-center py-16">
                <Spinner />
              </div>
            ) : conversation.isError ? (
              <Alert variant="danger">{toUiError(conversation.error).message}</Alert>
            ) : (
              <MessageThread
                messages={threadMessages}
                pending={send.isPending}
                onRetry={retry}
                retrying={send.isPending}
                hasOlder={Boolean(conversation.data?.olderCursor)}
                loadingOlder={loadOlder.isPending}
                onLoadOlder={() => {
                  const cursor = conversation.data?.olderCursor;
                  if (cursor) loadOlder.mutate(cursor);
                }}
                renderFeedback={(m) =>
                  m.status === 'ok' ? (
                    <FeedbackControls message={m} conversationId={conversationId} />
                  ) : null
                }
              />
            )}
          </div>

          <div className="border-t px-4 py-3">
            <Composer
              disabled={!conversationId}
              pending={send.isPending}
              onSend={(kind, content) => void sendMessage(kind, content)}
            />
          </div>
        </section>
      </div>
    </>
  );
}
