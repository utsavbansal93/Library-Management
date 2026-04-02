import { get, post, put, del } from './client';
import type {
  ArtifactSummary, ArtifactDetail, ArtifactCreate, ArtifactUpdate,
  CopyCreate, CopyDetail,
} from '../types';

export interface ArtifactListParams {
  format?: string;
  publisher?: string;
  location?: string;
  owner?: string;
  q?: string;
  skip?: number;
  limit?: number;
}

export function listArtifacts(params?: ArtifactListParams): Promise<ArtifactSummary[]> {
  const sp = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') sp.set(k, String(v));
    });
  }
  const qs = sp.toString();
  return get<ArtifactSummary[]>(`/artifacts${qs ? `?${qs}` : ''}`);
}

export function getArtifact(id: string): Promise<ArtifactDetail> {
  return get<ArtifactDetail>(`/artifacts/${id}`);
}

export function createArtifact(data: ArtifactCreate): Promise<ArtifactDetail> {
  return post<ArtifactDetail>('/artifacts', data);
}

export function updateArtifact(id: string, data: ArtifactUpdate): Promise<ArtifactDetail> {
  return put<ArtifactDetail>(`/artifacts/${id}`, data);
}

export function deleteArtifact(id: string): Promise<void> {
  return del<void>(`/artifacts/${id}`);
}

export function createCopy(artifactId: string, data: CopyCreate): Promise<CopyDetail> {
  return post<CopyDetail>(`/artifacts/${artifactId}/copies`, data);
}

export function coverUrl(artifactId: string): string {
  return `/api/artifacts/${artifactId}/cover`;
}
