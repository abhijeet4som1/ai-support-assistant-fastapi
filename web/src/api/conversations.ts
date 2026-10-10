import { useMutation, useQueryClient } from '@tanstack/react-query';

import { $api, apiClient } from './client';
import { companyKeys } from './companies';
import { type Conversation, type Coverage, type Message, type MessageKind } from './types';

export const conversationKeys = {
  list: ['get', '/api/conversations'] as const,
};

/** Messages loaded per page of a conversation; older pages are fetched on demand. */
export const MESSAGE_PAGE_SIZE = 50;

export interface ConversationFilters {
  companyId?: string;
  coverage?: Coverage;
  limit?: number;
}

/** Cursor-paginated conversation list; pages are `{ items, nextCursor }`. */
export function useConversationsInfinite(
  filters: ConversationFilters,
  options: { enabled?: boolean } = {},
) {
  return $api.useInfiniteQuery(
    'get',
    '/api/conversations',
    { params: { query: { ...filters, limit: filters.limit ?? 20 } } },
    {
      pageParamName: 'cursor',
      initialPageParam: undefined,
      getNextPageParam: (last) => last.nextCursor,
      enabled: options.enabled ?? true,
    },
  );
}

/** Cached shape of a conversation: the newest page plus every older page loaded so far. */
export interface ConversationData {
  conversation: Conversation;
  /** Present while older messages exist that are not loaded yet. */
  olderCursor?: string;
}

/** Conversation with its newest messages: `data.conversation`, `data.olderCursor`. */
export const conversationQuery = (conversationId: string) =>
  $api.queryOptions('get', '/api/conversations/{conversationId}', {
    params: { path: { conversationId }, query: { limit: MESSAGE_PAGE_SIZE } },
  });

/** Fetches the page before `olderCursor` and prepends it to the cached conversation. */
export function useLoadOlderMessages(conversationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (before: string) =>
      (
        await apiClient.GET('/api/conversations/{conversationId}', {
          params: { path: { conversationId }, query: { before, limit: MESSAGE_PAGE_SIZE } },
        })
      ).data!,
    onSuccess: (page) => {
      qc.setQueryData(
        conversationQuery(conversationId).queryKey,
        (prev: ConversationData | undefined): ConversationData | undefined => {
          if (!prev) return prev;
          const known = new Set(prev.conversation.messages.map((m) => m.id));
          const older = page.conversation.messages.filter((m) => !known.has(m.id));
          return {
            conversation: {
              ...prev.conversation,
              messages: [...older, ...prev.conversation.messages],
            },
            olderCursor: page.olderCursor,
          };
        },
      );
    },
  });
}

export function useCreateConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (companyId: string) =>
      (await apiClient.POST('/api/conversations', { body: { companyId } })).data!.conversation,
    onSuccess: (conversation) => {
      qc.setQueryData(conversationQuery(conversation.summary.id).queryKey, { conversation });
      void qc.invalidateQueries({ queryKey: conversationKeys.list });
      void qc.invalidateQueries({ queryKey: companyKeys.list });
    },
  });
}

export interface SendArgs {
  conversationId: string;
  kind: MessageKind;
  content: string;
}

/** Appends both returned messages to the cached conversation (no full refetch needed). */
export function useSendMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ conversationId, kind, content }: SendArgs) =>
      (
        await apiClient.POST('/api/conversations/{conversationId}/messages', {
          params: { path: { conversationId } },
          body: { kind, content },
        })
      ).data!,
    onSuccess: (out, { conversationId }) => {
      qc.setQueryData(
        conversationQuery(conversationId).queryKey,
        (prev: ConversationData | undefined): ConversationData | undefined => {
          if (!prev) return prev;
          const messages = [
            ...dropRetriedTurn(prev.conversation.messages, out.userMessage),
            out.userMessage,
            out.assistantMessage,
          ];
          // Only the loaded pages are in memory, so the count is adjusted, not recomputed.
          const added = messages.length - prev.conversation.messages.length;
          return {
            ...prev,
            conversation: {
              summary: {
                ...prev.conversation.summary,
                title: prev.conversation.summary.title || out.userMessage.content,
                messageCount: prev.conversation.summary.messageCount + added,
                lastCoverage:
                  out.assistantMessage.guidance?.coverage ?? prev.conversation.summary.lastCoverage,
                lastMessageAt: out.assistantMessage.createdAt,
              },
              messages,
            },
          };
        },
      );
      void qc.invalidateQueries({ queryKey: conversationKeys.list });
    },
  });
}

/** A retry of a failed turn reuses the user message id: remove the stale pair before appending. */
function dropRetriedTurn(messages: Message[], userMessage: Message) {
  const idx = messages.findIndex((m) => m.id === userMessage.id);
  return idx === -1 ? messages : messages.slice(0, idx);
}
