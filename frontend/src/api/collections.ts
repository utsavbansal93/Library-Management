import { get } from './client';
import type { CollectionSummary, CollectionDetail, CollectionTree } from '../types';

export function listCollections(tree?: boolean): Promise<CollectionSummary[] | CollectionTree[]> {
  return get(`/collections${tree ? '?tree=true' : ''}`);
}

export function getCollection(id: string): Promise<CollectionDetail> {
  return get<CollectionDetail>(`/collections/${id}`);
}
