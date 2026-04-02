import { get } from './client';
import type { ArcSummary, ArcDetail, ArcTree } from '../types';

export function listArcs(tree?: boolean): Promise<ArcSummary[] | ArcTree[]> {
  return get(`/arcs${tree ? '?tree=true' : ''}`);
}

export function getArc(id: string): Promise<ArcDetail> {
  return get<ArcDetail>(`/arcs/${id}`);
}
