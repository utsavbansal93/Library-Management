import { get, post, put, del } from './client';
import type { WorkSummary, WorkDetail, WorkCreate, WorkUpdate } from '../types';

export interface WorkListParams {
  work_type?: string;
  collection?: string;
  arc?: string;
  q?: string;
  skip?: number;
  limit?: number;
}

export function listWorks(params?: WorkListParams): Promise<WorkSummary[]> {
  const sp = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') sp.set(k, String(v));
    });
  }
  const qs = sp.toString();
  return get<WorkSummary[]>(`/works${qs ? `?${qs}` : ''}`);
}

export function getWork(id: string): Promise<WorkDetail> {
  return get<WorkDetail>(`/works/${id}`);
}

export function createWork(data: WorkCreate): Promise<WorkDetail> {
  return post<WorkDetail>('/works', data);
}

export function updateWork(id: string, data: WorkUpdate): Promise<WorkDetail> {
  return put<WorkDetail>(`/works/${id}`, data);
}

export function deleteWork(id: string): Promise<void> {
  return del<void>(`/works/${id}`);
}
