import { get } from './client';
import type { CreatorSummary, CreatorDetail } from '../types';

export function listCreators(q?: string): Promise<CreatorSummary[]> {
  return get<CreatorSummary[]>(`/creators${q ? `?q=${encodeURIComponent(q)}` : ''}`);
}

export function getCreator(id: string): Promise<CreatorDetail> {
  return get<CreatorDetail>(`/creators/${id}`);
}
