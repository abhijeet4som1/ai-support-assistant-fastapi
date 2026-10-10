import { type Coverage } from '@/api/types';

import { oneOf } from './guards';

export const COVERAGES = [
  'covered',
  'partial',
  'not_covered',
] as const satisfies readonly Coverage[];
export const isCoverage = oneOf(COVERAGES);
