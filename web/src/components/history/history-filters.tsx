import { Trans, useLingui } from '@lingui/react/macro';

import { type Company, type Coverage } from '@/api/types';
import { Label } from '@/components/ui/label';
import { isCoverage } from '@/lib/coverage';

export interface HistoryFilterValues {
  companyId?: string;
  coverage?: Coverage;
}

export interface HistoryFiltersProps {
  companies: Company[];
  value: HistoryFilterValues;
  onChange: (next: HistoryFilterValues) => void;
}

const selectClass =
  'bg-surface text-foreground focus-visible:ring-ring h-9 rounded-md border px-3 text-sm shadow-xs focus-visible:ring-2 focus-visible:outline-hidden';

export function HistoryFilters({ companies, value, onChange }: HistoryFiltersProps) {
  const { t } = useLingui();
  return (
    <div className="flex flex-wrap items-center gap-6">
      <div className="flex items-center gap-2">
        <Label htmlFor="filter-company">
          <Trans>Company</Trans>
        </Label>
        <select
          id="filter-company"
          className={selectClass}
          value={value.companyId ?? ''}
          onChange={(e) => onChange({ ...value, companyId: e.target.value || undefined })}
        >
          <option value="">{t`All companies`}</option>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <Label htmlFor="filter-coverage">
          <Trans>Coverage</Trans>
        </Label>
        <select
          id="filter-coverage"
          className={selectClass}
          value={value.coverage ?? ''}
          onChange={(e) =>
            onChange({
              ...value,
              coverage: isCoverage(e.target.value) ? e.target.value : undefined,
            })
          }
        >
          <option value="">{t`Any coverage`}</option>
          <option value="covered">{t`Covered`}</option>
          <option value="partial">{t`Partially covered`}</option>
          <option value="not_covered">{t`Not covered`}</option>
        </select>
      </div>
    </div>
  );
}
