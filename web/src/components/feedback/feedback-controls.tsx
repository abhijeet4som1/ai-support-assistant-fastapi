import { Trans, useLingui } from '@lingui/react/macro';
import { useAtomValue } from 'jotai';
import { ThumbsDown, ThumbsUp } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import { toUiError } from '@/api/errors';
import { useSubmitFeedback } from '@/api/feedback';
import { type Message } from '@/api/types';
import { userAtom } from '@/auth/atoms';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { FormField } from '@/components/ui/form-field';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/cn';
import { fieldProps } from '@/lib/form';

export interface FeedbackControlsProps {
  message: Message;
  conversationId: string;
}

/** Thumbs up / down on an assistant answer. Thumbs down asks what was wrong and for the right answer. */
export function FeedbackControls({ message, conversationId }: FeedbackControlsProps) {
  const { t } = useLingui();
  const user = useAtomValue(userAtom);
  const submit = useSubmitFeedback(conversationId);
  const [open, setOpen] = useState(false);
  const [whatWasWrong, setWhatWasWrong] = useState('');
  const [correctedAnswer, setCorrectedAnswer] = useState(message.guidance?.recommendedReply ?? '');
  const [errors, setErrors] = useState<{ correctedAnswer?: string; form?: string }>({});

  const mine = message.feedback?.find((f) => f.user?.id === user?.id);
  const others = (message.feedback ?? []).filter((f) => f.user?.id !== user?.id);

  const rateUp = async () => {
    try {
      await submit.mutateAsync({ messageId: message.id, rating: 'up' });
      toast.success(t`Thanks, marked as helpful`);
    } catch (err) {
      toast.error(toUiError(err).message);
    }
  };

  const rateDown = async () => {
    setErrors({});
    if (!correctedAnswer.trim()) {
      setErrors({ correctedAnswer: t`Provide the answer the assistant should have given` });
      return;
    }
    try {
      await submit.mutateAsync({
        messageId: message.id,
        rating: 'down',
        whatWasWrong,
        correctedAnswer,
      });
      setOpen(false);
      toast.success(t`Correction saved. It will guide similar answers for this company.`);
    } catch (err) {
      const ui = toUiError(err);
      if (ui.kind === 'validation' && ui.fields.correctedAnswer)
        setErrors({ correctedAnswer: ui.fields.correctedAnswer });
      else setErrors({ form: ui.message });
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      <span className="text-muted-foreground">
        <Trans>Was this helpful?</Trans>
      </span>
      <Button
        size="sm"
        variant={mine?.rating === 'up' ? 'secondary' : 'ghost'}
        aria-pressed={mine?.rating === 'up'}
        aria-label={t`Helpful`}
        onClick={() => void rateUp()}
        loading={submit.isPending && !open}
      >
        <ThumbsUp aria-hidden />
      </Button>
      <Button
        size="sm"
        variant={mine?.rating === 'down' ? 'secondary' : 'ghost'}
        aria-pressed={mine?.rating === 'down'}
        aria-label={t`Needs correction`}
        onClick={() => setOpen(true)}
      >
        <ThumbsDown aria-hidden />
      </Button>
      {mine?.rating === 'down' ? (
        <span className={cn('text-muted-foreground')}>
          <Trans>You submitted a correction.</Trans>
        </span>
      ) : null}
      {others.length ? (
        <span className="text-muted-foreground">
          <Trans>
            {others.length} other rating(s):{' '}
            {others
              .map((f) => `${f.user?.displayName ?? '?'} ${f.rating === 'up' ? '👍' : '👎'}`)
              .join(', ')}
          </Trans>
        </span>
      ) : null}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              <Trans>What should the answer have been?</Trans>
            </DialogTitle>
            <DialogDescription>
              <Trans>
                Your correction is stored for this company and shown to the assistant when similar
                customer messages come in. It never overrides the guidelines.
              </Trans>
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {errors.form ? <Alert variant="danger">{errors.form}</Alert> : null}
            <FormField
              htmlFor="what-was-wrong"
              label={<Trans>What was wrong?</Trans>}
              hint={<Trans>Optional</Trans>}
            >
              <Textarea
                id="what-was-wrong"
                rows={2}
                value={whatWasWrong}
                onChange={(e) => setWhatWasWrong(e.target.value)}
              />
            </FormField>
            <FormField
              htmlFor="corrected-answer"
              label={<Trans>Correct answer</Trans>}
              error={errors.correctedAnswer}
            >
              <Textarea
                {...fieldProps('corrected-answer', errors.correctedAnswer)}
                rows={6}
                value={correctedAnswer}
                onChange={(e) => setCorrectedAnswer(e.target.value)}
              />
            </FormField>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              <Trans>Cancel</Trans>
            </Button>
            <Button onClick={() => void rateDown()} loading={submit.isPending}>
              <Trans>Save correction</Trans>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
