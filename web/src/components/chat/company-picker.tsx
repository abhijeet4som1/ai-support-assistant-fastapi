import { Trans, useLingui } from '@lingui/react/macro';
import { Link } from '@tanstack/react-router';
import { Building2 } from 'lucide-react';

import { type Company } from '@/api/types';
import { Label } from '@/components/ui/label';

export interface CompanyPickerProps {
  companies: Company[];
  value?: string;
  onChange: (companyId: string) => void;
}

export function CompanyPicker({ companies, value, onChange }: CompanyPickerProps) {
  const { t } = useLingui();
  const ready = companies.filter((c) => c.activeGuidelines);
  const notReady = companies.filter((c) => !c.activeGuidelines);
  return (
    <div className="space-y-2">
      <Label htmlFor="company-picker">
        <Trans>Company</Trans>
      </Label>
      <div className="relative">
        <Building2
          className="text-muted-foreground pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2"
          aria-hidden
        />
        <select
          id="company-picker"
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          className="bg-surface text-foreground focus-visible:ring-ring shadow-xs focus-visible:outline-hidden h-9 w-full rounded-md border py-1 pl-9 pr-3 text-sm focus-visible:ring-2"
        >
          <option value="" disabled>
            {t`Select a company`}
          </option>
          {ready.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
          {notReady.length ? (
            <optgroup label={t`No guidelines yet`}>
              {notReady.map((c) => (
                <option key={c.id} value={c.id} disabled>
                  {c.name}
                </option>
              ))}
            </optgroup>
          ) : null}
        </select>
      </div>
      {companies.length === 0 ? (
        <p className="text-muted-foreground text-xs">
          <Trans>
            No companies yet.{' '}
            <Link to="/companies/new" className="text-primary underline">
              Add one
            </Link>
            .
          </Trans>
        </p>
      ) : null}
    </div>
  );
}
