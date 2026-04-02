import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getCollection } from '../api/collections';

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full bg-surface-container-highest px-2 py-0.5 font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
      {children}
    </span>
  );
}

function ProgressBar({ owned, total }: { owned: number; total: number }) {
  const pct = total > 0 ? Math.round((owned / total) * 100) : 0;
  return (
    <div className="w-full">
      <div className="mb-1 flex items-center justify-between">
        <span className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
          Completion
        </span>
        <span className="font-body text-xs text-on-surface-variant">
          {owned}/{total} ({pct}%)
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-surface-container-highest">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function CollectionDetail() {
  const { collectionId: collection_id } = useParams<{ collectionId: string }>();
  const {
    data: collection,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['collection', collection_id],
    queryFn: () => getCollection(collection_id!),
    enabled: !!collection_id,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
        <div className="mb-6 h-12 w-64 animate-pulse rounded-xl bg-surface-container-low" />
        <div className="mb-4 h-4 w-48 animate-pulse rounded bg-surface-container-low" />
        <div className="mb-8 h-2 w-full animate-pulse rounded-full bg-surface-container-low" />
        <div className="flex flex-col gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-14 animate-pulse rounded-xl bg-surface-container-low" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
        <div className="rounded-2xl bg-error-container p-6 text-on-error-container">
          <p className="font-body text-sm">
            Failed to load collection. {error instanceof Error ? error.message : 'Unknown error.'}
          </p>
        </div>
      </div>
    );
  }

  if (!collection) return null;

  const works = collection.works ?? [];
  const children = collection.children ?? [];
  const sortedWorks = [...works].sort(
    (a, b) => (a.sequence_number ?? 0) - (b.sequence_number ?? 0),
  );

  // Count works that have an artifact (very rough heuristic: works with artifact_works)
  // Since WorkInCollection only has WorkBrief, we count all works for total
  // and can't determine which have artifacts at this level. Show total count only.
  const totalWorks = works.length;

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      {/* Hero */}
      <header className="mb-8">
        <div className="mb-2 flex items-center gap-3">
          <h1 className="font-headline text-5xl text-primary">{collection.name}</h1>
          <Badge>{collection.collection_type}</Badge>
        </div>
        {collection.description && (
          <p className="mt-2 font-body text-base text-on-surface-variant">
            {collection.description}
          </p>
        )}
      </header>

      {/* Progress */}
      {totalWorks > 0 && (
        <div className="mb-10">
          <ProgressBar owned={totalWorks} total={totalWorks} />
        </div>
      )}

      {/* Works list */}
      {sortedWorks.length > 0 && (
        <section className="mb-10">
          <h2 className="mb-4 font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
            Works
          </h2>
          <div className="overflow-hidden rounded-2xl bg-surface-container-lowest">
            {sortedWorks.map((entry, idx) => (
              <div
                key={entry.work.work_id}
                className={`flex items-center gap-4 px-5 py-3 ${idx > 0 ? 'bg-surface-container-lowest' : ''}`}
              >
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface-container-highest font-label text-[10px] font-bold text-on-surface-variant">
                  {entry.sequence_number ?? idx + 1}
                </span>
                <Link
                  to={`/works/${entry.work.work_id}`}
                  className="min-w-0 flex-1 font-body text-sm font-medium text-on-surface hover:underline"
                >
                  {entry.work.title}
                </Link>
                <Badge>{entry.work.work_type}</Badge>
              </div>
            ))}
          </div>
        </section>
      )}

      {sortedWorks.length === 0 && (
        <p className="mb-10 py-8 text-center font-body text-sm text-on-surface-variant">
          No works in this collection yet.
        </p>
      )}

      {/* Sub-collections */}
      {children.length > 0 && (
        <section>
          <h2 className="mb-4 font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
            Sub-Collections
          </h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {children.map((child) => (
              <Link
                key={child.collection_id}
                to={`/collections/${child.collection_id}`}
                className="group rounded-2xl bg-surface-container-lowest p-5 transition-shadow hover:shadow-md"
              >
                <h3 className="font-body text-sm font-medium text-on-surface group-hover:underline">
                  {child.name}
                </h3>
                <Badge>{child.collection_type}</Badge>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
