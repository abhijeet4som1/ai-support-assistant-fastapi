import { Trans, useLingui } from '@lingui/react/macro';
import { FileUp, Upload, X } from 'lucide-react';
import { useId, useRef, useState } from 'react';
import { toast } from 'sonner';

import { toUiError, type UiError } from '@/api/errors';
import { useUploadGuidelines } from '@/api/guidelines';
import { type GuidelineVersionSummary } from '@/api/types';
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
import { cn } from '@/lib/cn';
import { ACCEPTED_GUIDELINE_EXTENSIONS, fileExtension, MAX_GUIDELINE_MB } from '@/lib/files';
import { formatBytes, formatDateTime } from '@/lib/format';

export interface GuidelineUploadProps {
  companyId: string;
  /** Latest version the page displayed; sent as X-Expected-Version to detect concurrent uploads. */
  latestVersion?: GuidelineVersionSummary;
  onUploaded?: (version: GuidelineVersionSummary) => void;
}

type Conflict = Extract<UiError, { code: 'guidelines_conflict' }>;

export function GuidelineUpload({ companyId, latestVersion, onUploaded }: GuidelineUploadProps) {
  const { t } = useLingui();
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState<Conflict | null>(null);
  const [dragging, setDragging] = useState(false);
  const upload = useUploadGuidelines();

  const pick = (f: File | undefined) => {
    setError(null);
    if (!f) return;
    const ext = fileExtension(f.name);
    if (!ACCEPTED_GUIDELINE_EXTENSIONS.includes(ext)) {
      setError(
        t`Unsupported file type. Upload a ${ACCEPTED_GUIDELINE_EXTENSIONS.join(', ')} file.`,
      );
      setFile(null);
      return;
    }
    if (f.size > MAX_GUIDELINE_MB * 1024 * 1024) {
      setError(t`The file is larger than ${MAX_GUIDELINE_MB} MB.`);
      setFile(null);
      return;
    }
    setFile(f);
  };

  const submit = async (force = false) => {
    if (!file) return;
    setError(null);
    try {
      const version = await upload.mutateAsync({
        companyId,
        file,
        expectedVersionId: force ? undefined : latestVersion?.id,
      });
      setConflict(null);
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
      // Same content as the active version: the api returns it unchanged and queues nothing.
      if (latestVersion?.id === version.id) {
        toast.info(t`This file is identical to the current guidelines. Nothing to process.`);
        return;
      }
      toast.success(t`Guidelines uploaded. Processing has started.`);
      onUploaded?.(version);
    } catch (err) {
      const ui = toUiError(err);
      if (ui.kind === 'conflict' && ui.code === 'guidelines_conflict') {
        setConflict(ui);
        return;
      }
      if (ui.kind === 'upload') {
        setError(ui.detail ? `${ui.message} (${ui.detail})` : ui.message);
        return;
      }
      setError(
        ui.kind === 'network'
          ? t`Cannot reach the server. Check your connection and try again.`
          : ui.message,
      );
    }
  };

  return (
    <div className="space-y-3">
      <label
        htmlFor={inputId}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          pick(e.dataTransfer.files[0]);
        }}
        className={cn(
          'hover:bg-muted/50 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed px-6 py-8 text-center transition-colors',
          dragging ? 'border-primary bg-primary-soft/40' : 'border-border',
        )}
      >
        <FileUp className="text-muted-foreground size-8" aria-hidden />
        <span className="text-sm">
          <span className="text-primary font-medium">
            <Trans>Choose a file</Trans>
          </span>{' '}
          <Trans>or drag and drop</Trans>
        </span>
        <span className="text-muted-foreground text-xs">
          <Trans>TXT, MD, PDF or DOCX up to {MAX_GUIDELINE_MB} MB</Trans>
        </span>
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          className="sr-only"
          accept={ACCEPTED_GUIDELINE_EXTENSIONS.join(',')}
          onChange={(e) => pick(e.target.files?.[0])}
        />
      </label>

      {file ? (
        <div className="bg-muted/60 flex items-center justify-between gap-3 rounded-md px-3 py-2 text-sm">
          <span className="truncate">
            {file.name} <span className="text-muted-foreground">({formatBytes(file.size)})</span>
          </span>
          <div className="flex shrink-0 items-center gap-2">
            <Button size="sm" onClick={() => void submit(false)} loading={upload.isPending}>
              <Upload aria-hidden />
              {latestVersion ? <Trans>Replace guidelines</Trans> : <Trans>Upload guidelines</Trans>}
            </Button>
            <Button
              size="icon"
              variant="ghost"
              aria-label={t`Remove file`}
              onClick={() => setFile(null)}
            >
              <X aria-hidden />
            </Button>
          </div>
        </div>
      ) : null}

      {error ? <Alert variant="danger">{error}</Alert> : null}

      <Dialog open={conflict !== null} onOpenChange={(open) => !open && setConflict(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              <Trans>Someone else uploaded guidelines</Trans>
            </DialogTitle>
            <DialogDescription>
              {conflict?.uploadedBy ? (
                <Trans>
                  {conflict.uploadedBy} uploaded new guidelines on{' '}
                  {formatDateTime(conflict.uploadedAt)}, after you opened this page. Replace their
                  version with your file?
                </Trans>
              ) : (
                <Trans>
                  New guidelines were uploaded after you opened this page. Replace them with your
                  file?
                </Trans>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConflict(null)}>
              <Trans>Keep theirs</Trans>
            </Button>
            <Button variant="danger" onClick={() => void submit(true)} loading={upload.isPending}>
              <Trans>Replace anyway</Trans>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
