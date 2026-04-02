import { get, put } from './client';
import type { FlagSummary, FlagUpdate } from '../types';

export function listFlags(params?: { type?: string; status?: string }): Promise<FlagSummary[]> {
  const sp = new URLSearchParams();
  if (params?.type) sp.set('type', params.type);
  if (params?.status) sp.set('status', params.status);
  const qs = sp.toString();
  return get<FlagSummary[]>(`/flags${qs ? `?${qs}` : ''}`);
}

export function updateFlag(id: string, data: FlagUpdate): Promise<FlagSummary> {
  return put<FlagSummary>(`/flags/${id}`, data);
}
