import { get, post } from './client';
import type { ActivityCreate, ActivityEntry } from '../types';

export function listActivity(params?: { work_id?: string; profile?: string }): Promise<ActivityEntry[]> {
  const sp = new URLSearchParams();
  if (params?.work_id) sp.set('work_id', params.work_id);
  if (params?.profile) sp.set('profile', params.profile);
  const qs = sp.toString();
  return get<ActivityEntry[]>(`/activity${qs ? `?${qs}` : ''}`);
}

export function logActivity(data: ActivityCreate): Promise<ActivityEntry> {
  return post<ActivityEntry>('/activity', data);
}
