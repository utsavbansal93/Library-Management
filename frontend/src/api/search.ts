import { get } from './client';
import type { SearchResults } from '../types';

export function globalSearch(q: string): Promise<SearchResults> {
  return get<SearchResults>(`/search?q=${encodeURIComponent(q)}`);
}
