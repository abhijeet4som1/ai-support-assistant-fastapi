import { useMutation, useQueryClient } from '@tanstack/react-query';

import { $api, apiClient } from './client';
import { conversationQuery } from './conversations';
import { type Conversation, type Correction, type FeedbackRating } from './types';

export const correctionKeys = { all: ['get', '/api/companies/{companyId}/corrections'] as const };

/** Corrections of a company (active and inactive): `data.items`. */
export const correctionsQuery = (companyId: string, includeInactive = true) =>
  $api.queryOptions('get', '/api/companies/{companyId}/corrections', {
    params: { path: { companyId }, query: { includeInactive } },
  });

export interface SubmitFeedbackArgs {
  messageId: string;
  rating: FeedbackRating;
  whatWasWrong?: string;
  correctedAnswer?: string;
}

/** Rates an assistant message; the returned correction is merged into the cached conversation. */
export function useSubmitFeedback(conversationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ messageId, ...body }: SubmitFeedbackArgs) =>
      (
        await apiClient.PUT('/api/messages/{messageId}/feedback', {
          params: { path: { messageId } },
          body,
        })
      ).data!.correction,
    onSuccess: (correction) => {
      qc.setQueryData(
        conversationQuery(conversationId).queryKey,
        (prev: { conversation: Conversation } | undefined) => {
          if (!prev) return prev;
          return {
            conversation: {
              ...prev.conversation,
              messages: prev.conversation.messages.map((m) => {
                if (m.id !== correction.messageId) return m;
                const others = (m.feedback ?? []).filter((f) => f.user.id !== correction.user.id);
                return {
                  ...m,
                  feedback: [
                    ...others,
                    {
                      id: correction.id,
                      rating: correction.rating,
                      whatWasWrong: correction.whatWasWrong,
                      correctedAnswer: correction.correctedAnswer,
                      user: correction.user,
                      createdAt: correction.createdAt,
                    },
                  ],
                };
              }),
            },
          };
        },
      );
      void qc.invalidateQueries({ queryKey: correctionKeys.all });
    },
  });
}

export function useUpdateCorrection(companyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ correctionId, active }: { correctionId: string; active: boolean }) =>
      (
        await apiClient.PATCH('/api/corrections/{correctionId}', {
          params: { path: { correctionId } },
          body: { active },
        })
      ).data!.correction,
    onSuccess: (updated) => {
      qc.setQueryData(
        correctionsQuery(companyId, true).queryKey,
        (prev: { items: Correction[] } | undefined) =>
          prev ? { items: prev.items.map((c) => (c.id === updated.id ? updated : c)) } : prev,
      );
      void qc.invalidateQueries({ queryKey: correctionKeys.all });
    },
  });
}
