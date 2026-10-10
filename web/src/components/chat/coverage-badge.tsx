import { Trans } from '@lingui/react/macro';
import { AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react';

import { Badge } from '@/components/ui/badge';

export function CoverageBadge({ coverage }: { coverage?: string }) {
  switch (coverage) {
    case 'covered':
      return (
        <Badge variant="success">
          <CheckCircle2 aria-hidden />
          <Trans>Covered by guidelines</Trans>
        </Badge>
      );
    case 'partial':
      return (
        <Badge variant="warning">
          <AlertTriangle aria-hidden />
          <Trans>Partially covered</Trans>
        </Badge>
      );
    case 'not_covered':
      return (
        <Badge variant="danger">
          <HelpCircle aria-hidden />
          <Trans>Not covered</Trans>
        </Badge>
      );
    default:
      return null;
  }
}
