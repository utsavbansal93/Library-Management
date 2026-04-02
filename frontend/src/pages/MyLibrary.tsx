import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listArtifacts } from '../api/artifacts';
import type { ArtifactListParams } from '../api/artifacts';
import { cn } from '../lib/utils';
import ArtifactCard from '../components/cards/ArtifactCard';
import ArtifactListRow from '../components/cards/ArtifactListRow';
import ViewToggle from '../components/shared/ViewToggle';
import SortDropdown from '../components/shared/SortDropdown';
import Pagination from '../components/shared/Pagination';
import EmptyState from '../components/shared/EmptyState';

const VIEW_STORAGE_KEY = 'alexandria-view-mode';
const PER_PAGE = 20;

type SortOption = 'title' | 'date_added' | 'edition_year';

function getStoredView(): 'grid' | 'list' {
  const stored = localStorage.getItem(VIEW_STORAGE_KEY);
  return stored === 'list' ? 'list' : 'grid';
}

export default function MyLibrary() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(getStoredView);

  const format = searchParams.get('format') ?? undefined;
  const q = searchParams.get('q') ?? '';
  const sort = (searchParams.get('sort') as SortOption) ?? 'title';
  const page = parseInt(searchParams.get('page') ?? '1', 10);

  // Debounced search: local input state syncs to URL after 300ms
  const [searchText, setSearchText] = useState(q);
  useEffect(() => {
    setSearchText(q);
  }, [q]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchText !== q) {
        updateParam('q', searchText);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchText]); // eslint-disable-line react-hooks/exhaustive-deps

  // Persist view mode
  useEffect(() => {
    localStorage.setItem(VIEW_STORAGE_KEY, viewMode);
  }, [viewMode]);

  const params: ArtifactListParams = {
    format: format,
    q: q || undefined,
    sort,
    offset: (page - 1) * PER_PAGE,
    limit: PER_PAGE,
  };

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['artifacts', params],
    queryFn: () => listArtifacts(params),
  });

  const items = data?.items ?? [];
  const totalItems = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalItems / PER_PAGE));

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    // Reset page when filters change
    if (key !== 'page') next.delete('page');
    setSearchParams(next);
  }

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      {/* Header */}
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">Master Ledger</h1>
        <p className="mt-2 font-body text-base text-on-surface-variant">
          {isLoading
            ? 'Loading artifacts...'
            : `${totalItems} artifact${totalItems !== 1 ? 's' : ''} in your library`}
        </p>
      </header>

      {/* Toolbar */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Search */}
        <div className="relative max-w-md flex-1">
          <input
            type="text"
            placeholder="Search by title, publisher..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="w-full rounded-xl bg-surface-container-low px-4 py-3 pl-10 font-body text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <svg
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-on-surface-variant"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"
            />
          </svg>
        </div>

        <div className="flex items-center gap-3">
          <SortDropdown
            value={sort}
            onChange={(v: string) => updateParam('sort', v)}
            options={[
              { value: 'title', label: 'Title A-Z' },
              { value: 'date_added', label: 'Date Added' },
              { value: 'edition_year', label: 'Edition Year' },
            ]}
          />
          <ViewToggle view={viewMode} onChange={setViewMode} />
        </div>
      </div>

      {/* Content */}
      {isLoading && (
        <div
          className={cn(
            viewMode === 'grid'
              ? 'grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
              : 'flex flex-col gap-2',
          )}
        >
          {Array.from({ length: PER_PAGE }).map((_, i) => (
            <div
              key={i}
              className={cn(
                'animate-pulse rounded-2xl bg-surface-container-low',
                viewMode === 'grid' ? 'aspect-[2/3]' : 'h-20 w-full',
              )}
            />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-2xl bg-error-container p-6 text-on-error-container">
          <p className="font-body text-sm">
            Failed to load artifacts.{' '}
            {error instanceof Error ? error.message : 'Unknown error.'}
          </p>
        </div>
      )}

      {!isLoading && !isError && items.length === 0 && (
        <EmptyState
          icon="search_off"
          title="No artifacts found"
          description={
            q
              ? `No results for "${q}". Try a different search.`
              : 'Your library is empty. Add your first artifact to get started.'
          }
        />
      )}

      {!isLoading && !isError && items.length > 0 && (
        <>
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              {items.map((artifact) => (
                <ArtifactCard key={artifact.artifact_id} artifact={artifact} />
              ))}
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl bg-surface-container-low">
              <table className="w-full">
                <thead>
                  <tr className="bg-surface-container">
                    <th className="px-4 py-3 text-left">
                      <span className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
                        Title
                      </span>
                    </th>
                    <th className="px-4 py-3 text-left">
                      <span className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
                        Format
                      </span>
                    </th>
                    <th className="hidden px-4 py-3 text-left md:table-cell">
                      <span className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
                        Publisher
                      </span>
                    </th>
                    <th className="hidden px-4 py-3 text-left lg:table-cell">
                      <span className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
                        Owner
                      </span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((artifact) => (
                    <ArtifactListRow
                      key={artifact.artifact_id}
                      artifact={artifact}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          <div className="mt-8 flex justify-center">
            <Pagination
              page={page}
              totalPages={totalPages}
              onPageChange={(p: number) => updateParam('page', String(p))}
            />
          </div>
        </>
      )}
    </div>
  );
}
