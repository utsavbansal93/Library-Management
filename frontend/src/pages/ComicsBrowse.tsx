import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listArcs } from '../api/arcs';
import { listArtifacts } from '../api/artifacts';
import CoverImage from '../components/shared/CoverImage';
import type { ArcTree, ArtifactSummary } from '../types';

type Tab = 'arcs' | 'graphic-novels' | 'comic-issues';

const TABS: { key: Tab; label: string }[] = [
  { key: 'arcs', label: 'Arcs & Series' },
  { key: 'graphic-novels', label: 'Graphic Novels' },
  { key: 'comic-issues', label: 'Comic Issues' },
];

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

function ArtifactGrid({ artifacts }: { artifacts: ArtifactSummary[] }) {
  if (artifacts.length === 0) {
    return (
      <p className="py-12 text-center font-body text-sm text-on-surface-variant">
        No artifacts found in this category.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {artifacts.map((artifact) => (
        <Link
          key={artifact.artifact_id}
          to={`/artifacts/${artifact.artifact_id}`}
          className="group overflow-hidden rounded-2xl bg-surface-container-lowest transition-shadow hover:shadow-md"
        >
          <CoverImage
            artifactId={artifact.artifact_id}
            title={artifact.title}
            size="md"
            className="w-full"
          />
          <div className="p-3">
            <p className="font-body text-sm font-medium text-on-surface line-clamp-2 group-hover:underline">
              {artifact.title}
            </p>
            {artifact.publisher && (
              <p className="mt-1 font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
                {artifact.publisher}
              </p>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}

export default function ComicsBrowse() {
  const [activeTab, setActiveTab] = useState<Tab>('arcs');

  const { data: arcTree, isLoading: arcsLoading } = useQuery({
    queryKey: ['arcs', 'tree'],
    queryFn: () => listArcs(true) as Promise<ArcTree[]>,
    enabled: activeTab === 'arcs',
  });

  const { data: graphicNovels, isLoading: gnsLoading } = useQuery({
    queryKey: ['artifacts', { format: 'Graphic Novel' }],
    queryFn: () => listArtifacts({ format: 'Graphic Novel' }),
    enabled: activeTab === 'graphic-novels',
  });

  const { data: comicIssues, isLoading: issuesLoading } = useQuery({
    queryKey: ['artifacts', { format: 'Comic Issue' }],
    queryFn: () => listArtifacts({ format: 'Comic Issue' }),
    enabled: activeTab === 'comic-issues',
  });

  const isLoading =
    (activeTab === 'arcs' && arcsLoading) ||
    (activeTab === 'graphic-novels' && gnsLoading) ||
    (activeTab === 'comic-issues' && issuesLoading);

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">Comics</h1>
      </header>

      {/* Tab bar */}
      <div className="mb-8 flex gap-6">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`pb-2 font-label text-sm font-bold uppercase tracking-widest transition-colors ${
              activeTab === tab.key
                ? 'border-b-2 border-primary text-primary'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="aspect-[2/3] animate-pulse rounded-2xl bg-surface-container-low" />
          ))}
        </div>
      )}

      {/* Arcs tab */}
      {!isLoading && activeTab === 'arcs' && (
        <div className="rounded-2xl bg-surface-container-lowest p-4">
          {arcTree && arcTree.length > 0 ? (
            arcTree.map((arc) => <ArcTreeNode key={arc.arc_id} arc={arc} />)
          ) : (
            <p className="py-12 text-center font-body text-sm text-on-surface-variant">
              No story arcs found.
            </p>
          )}
        </div>
      )}

      {/* Graphic Novels tab */}
      {!isLoading && activeTab === 'graphic-novels' && (
        <ArtifactGrid artifacts={graphicNovels ?? []} />
      )}

      {/* Comic Issues tab */}
      {!isLoading && activeTab === 'comic-issues' && (
        <ArtifactGrid artifacts={comicIssues ?? []} />
      )}
    </div>
  );
}
