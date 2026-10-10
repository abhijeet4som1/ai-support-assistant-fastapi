import { Trans } from '@lingui/react/macro';
import { useAtomValue } from 'jotai';
import { WifiOff } from 'lucide-react';

import { networkProblemAtom } from '@/state/network';

export function NetworkBanner() {
  const problem = useAtomValue(networkProblemAtom);
  if (!problem) return null;
  return (
    <div
      role="alert"
      className="bg-warning-soft text-warning-soft-foreground border-warning/40 flex items-center justify-center gap-2 border-b px-4 py-2 text-sm"
    >
      <WifiOff className="size-4" aria-hidden />
      <Trans>Cannot reach the server. Retrying automatically…</Trans>
    </div>
  );
}
