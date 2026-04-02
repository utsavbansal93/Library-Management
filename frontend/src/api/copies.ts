import { put } from './client';
import type { CopyDetail } from '../types';

export function updateCopy(id: string, data: Partial<CopyDetail>): Promise<CopyDetail> {
  return put<CopyDetail>(`/copies/${id}`, data);
}

export function lendCopy(id: string, borrower_name: string): Promise<CopyDetail> {
  return put<CopyDetail>(`/copies/${id}/lend`, { borrower_name });
}

export function returnCopy(id: string, location?: string): Promise<CopyDetail> {
  return put<CopyDetail>(`/copies/${id}/return`, location ? { location } : {});
}
