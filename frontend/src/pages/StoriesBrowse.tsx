import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listArcs } from '../api/arcs';
import { listCollections } from '../api/collections';
import type { ArcTree, CollectionTree } from '../types';

function ArcTreeNode({ arc, depth = 0 }: { arc: ArcTree; depth?: number }) {
  const [open, setOpen] = useState(false);
  const hasChildren = arc.children && arc.children.length > 0;

  return (
    <div style={{ paddingLeft: depth > 0 ? '1.5rem' : 0 }}>
      <div className="flex items-center gap-2 rounded-xl px-3 py-2 hover:bg-surface-container-low">
        {hasChildren ? (
          <button onClick={() => setOpen(!open)} className="shrink-0">
            <span
              className={`material-symbols-outlined text-on-surface-variant text-lg transition-transform duration-200 ${open ? 'rotate-90' : ''}`}
            >
              chevron_right
            </span>
          </button>
        ) : (
          <span className="inline-block w-6" />
        )}
        <Link
          to={`/arcs/${arc.arc_id}`}
          className="min-w-0 flex-1 font-body text-sm font-medium text-on-surface hover:underline"
        >
          {arc.name}
        </Link>
        <div className="flex shrink-0 items-center gap-2">
          {arc.total_parts != null && (
            <span className="font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
              {arc.total_parts} parts
            </span>
          )}
          {arc.completion_status && (
            <span className="rounded-full bg-surface-container-highest px-2 py-0.5 font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
              {arc.completion_status}
            </span>
          )}
        </div>
      </div>
      {open && hasChildren && (
        <div className="mt-1 flex flex-col">
          {arc.children.map((child) => (
            <ArcTreeNode key={child.arc_id} arc={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function CollectionTreeNode({ col, depth = 0 }: { col: CollectionTree; depth?: number }) {
  const [open, setOpen] = useState(false);
  const hasChildren = col.children && col.children.length > 0;

  return (
    <div style={{ paddingLeft: depth > 0 ? '1.5rem' : 0 }}>
      <div className="flex items-center gap-2 rounded-xl px-3 py-2 hover:bg-surface-container-low">
        {hasChildren ? (
          <button onClick={() => setOpen(!open)} className="shrink-0">
            <span
              className={`material-symbols-outlined text-on-surface-variant text-lg transition-transform duration-200 ${open ? 'rotate-90' : ''}`}
            >
              chevron_right
            </span>
          </button>
        ) : (
          <span className="inline-block w-6" />
        )}
        <Link
          to={`/collections/${col.collection_id}`}
          className="min-w-0 flex-1 font-body text-sm font-medium text-on-surface hover:underline"
        >
          {col.name}
        </Link>
        <span className="rounded-full bg-surface-container-highest px-2 py-0.5 font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          {col.collection_type}
        </span>
      </div>
      {open && hasChildren && (
        <div className="mt-1 flex flex-col">
          {col.children.map((child) => (
            <CollectionTreeNode key={child.collection_id} col={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function filterArcTree(nodes: ArcTree[], q: string): ArcTree[] {
  const lq = q.toLowerCase();
  return nodes.reduce<ArcTree[]>((acc, node) => {
    const filteredChildren = filterArcTree(node.children ?? [], q);
    if (node.name.toLowerCase().includes(lq) || filteredChildren.length > 0) {
      acc.push({ ...node, children: filteredChildren });
    }
    return acc;
  }, []);
}

function filterCollectionTree(nodes: CollectionTree[], q: string): CollectionTree[] {
  const lq = q.toLowerCase();
  return nodes.reduce<CollectionTree[]>((acc, node) => {
    const filteredChildren = filterCollectionTree(node.children ?? [], q);
    if (node.name.toLowerCase().includes(lq) || filteredChildren.length > 0) {
      acc.push({ ...node, children: filteredChildren });
    }
    return acc;
  }, []);
}

function countArcNodes(nodes: ArcTree[]): number {
  return nodes.reduce((n, a) => n + 1 + countArcNodes(a.children ?? []), 0);
}

function countCollectionNodes(nodes: CollectionTree[]): number {
  return nodes.reduce((n, c) => n + 1 + countCollectionNodes(c.children ?? []), 0);
}

type Tab = 'arcs' | 'collections';

export default function StoriesBrowse() {
  const [tab, setTab] = useState<Tab>('arcs');
  const [search, setSearch] = useState('');

  const { data: arcTree, isLoading: arcsLoading } = useQuery({
    queryKey: ['arcs', 'tree'],
    queryFn: () => listArcs(true) as Promise<ArcTree[]>,
  });

  const { data: collectionTree, isLoading: collectionsLoading } = useQuery({
    queryKey: ['collections', 'tree'],
    queryFn: () => listCollections(true) as Promise<CollectionTree[]>,
  });

  const filteredArcs = useMemo(
    () => (arcTree && search ? filterArcTree(arcTree, search) : arcTree ?? []),
    [arcTree, search],
  );

  const filteredCollections = useMemo(
    () => (collectionTree && search ? filterCollectionTree(collectionTree, search) : collectionTree ?? []),
    [collectionTree, search],
  );

  const isLoading = tab === 'arcs' ? arcsLoading : collectionsLoading;
  const arcCount = arcTree ? countArcNodes(arcTree) : 0;
  const colCount = collectionTree ? countCollectionNodes(collectionTree) : 0;

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <header className="mb-8">
        <h1 className="font-headline text-5xl text-primary">Stories & Series</h1>
        <p className="mt-2 font-body text-base text-on-surface-variant">
          Navigate your collection by narrative arcs and series timelines.
        </p>
      </header>

      {/* Search + Tabs */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between max-w-4xl">
        <div className="relative max-w-xs flex-1">
          <input
            type="text"
            placeholder="Search by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl bg-surface-container-low px-4 py-2.5 pl-10 font-body text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">
            search
          </span>
        </div>
        <div className="flex rounded-xl bg-surface-container-low p-1">
          <button
            onClick={() => setTab('arcs')}
            className={`rounded-lg px-4 py-1.5 font-label text-xs font-bold uppercase tracking-widest transition-colors ${
              tab === 'arcs'
                ? 'bg-primary text-on-primary'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Story Arcs ({arcCount})
          </button>
          <button
            onClick={() => setTab('collections')}
            className={`rounded-lg px-4 py-1.5 font-label text-xs font-bold uppercase tracking-widest transition-colors ${
              tab === 'collections'
                ? 'bg-primary text-on-primary'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Collections ({colCount})
          </button>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 15 }).map((_, i) => (
            <div key={i} className="h-8 animate-pulse rounded bg-surface-container-low w-full max-w-xl" />
          ))}
        </div>
      )}

      {/* Arcs tab */}
      {!isLoading && tab === 'arcs' && (
        <div className="rounded-2xl bg-surface-container-lowest p-4 max-w-4xl">
          {filteredArcs.length > 0 ? (
            filteredArcs.map((arc) => <ArcTreeNode key={arc.arc_id} arc={arc} />)
          ) : (
            <p className="py-12 text-center font-body text-sm text-on-surface-variant">
              {search ? `No story arcs matching "${search}".` : 'No story arcs found.'}
            </p>
          )}
        </div>
      )}

      {/* Collections tab */}
      {!isLoading && tab === 'collections' && (
        <div className="rounded-2xl bg-surface-container-lowest p-4 max-w-4xl">
          {filteredCollections.length > 0 ? (
            filteredCollections.map((col) => (
              <CollectionTreeNode key={col.collection_id} col={col} />
            ))
          ) : (
            <p className="py-12 text-center font-body text-sm text-on-surface-variant">
              {search ? `No collections matching "${search}".` : 'No collections found.'}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
