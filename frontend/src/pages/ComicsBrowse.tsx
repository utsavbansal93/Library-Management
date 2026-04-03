import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listArtifacts } from '../api/artifacts';
import CoverImage from '../components/shared/CoverImage';
import Pagination from '../components/shared/Pagination';
import type { ArtifactSummary } from '../types';

type Tab = 'graphic-novels' | 'comic-issues';

const TABS: { key: Tab; label: string }[] = [
  { key: 'graphic-novels', label: 'Graphic Novels' },
  { key: 'comic-issues', label: 'Comic Issues' },
];

const PAGE_SIZE = 40;

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
  const [activeTab, setActiveTab] = useState<Tab>('graphic-novels');
  const [gnPage, setGnPage] = useState(1);
  const [ciPage, setCiPage] = useState(1);

  const gnOffset = (gnPage - 1) * PAGE_SIZE;
  const ciOffset = (ciPage - 1) * PAGE_SIZE;

  const { data: graphicNovels, isLoading: gnsLoading } = useQuery({
    queryKey: ['artifacts', { format: 'Graphic Novel', offset: gnOffset, limit: PAGE_SIZE }],
    queryFn: () => listArtifacts({ format: 'Graphic Novel', offset: gnOffset, limit: PAGE_SIZE }),
    enabled: activeTab === 'graphic-novels',
  });

  const { data: comicIssues, isLoading: issuesLoading } = useQuery({
    queryKey: ['artifacts', { format: 'Comic Issue', offset: ciOffset, limit: PAGE_SIZE }],
    queryFn: () => listArtifacts({ format: 'Comic Issue', offset: ciOffset, limit: PAGE_SIZE }),
    enabled: activeTab === 'comic-issues',
  });

  const isLoading =
    (activeTab === 'graphic-novels' && gnsLoading) ||
    (activeTab === 'comic-issues' && issuesLoading);

  const gnTotal = graphicNovels?.total ?? 0;
  const ciTotal = comicIssues?.total ?? 0;
  const gnTotalPages = Math.ceil(gnTotal / PAGE_SIZE);
  const ciTotalPages = Math.ceil(ciTotal / PAGE_SIZE);

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">Comics</h1>
        <p className="mt-2 font-body text-base text-on-surface-variant">
          {activeTab === 'graphic-novels'
            ? `${gnTotal} graphic novel${gnTotal !== 1 ? 's' : ''}`
            : `${ciTotal} comic issue${ciTotal !== 1 ? 's' : ''}`}
        </p>
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

      {/* Graphic Novels tab */}
      {!isLoading && activeTab === 'graphic-novels' && (
        <>
          <ArtifactGrid artifacts={graphicNovels?.items ?? []} />
          {gnTotalPages > 1 && (
            <div className="mt-8">
              <Pagination page={gnPage} totalPages={gnTotalPages} onPageChange={setGnPage} />
            </div>
          )}
        </>
      )}

      {/* Comic Issues tab */}
      {!isLoading && activeTab === 'comic-issues' && (
        <>
          <ArtifactGrid artifacts={comicIssues?.items ?? []} />
          {ciTotalPages > 1 && (
            <div className="mt-8">
              <Pagination page={ciPage} totalPages={ciTotalPages} onPageChange={setCiPage} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
