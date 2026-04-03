import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { globalSearch } from '../api/search';
import CoverImage from '../components/shared/CoverImage';

const MAX_PER_TYPE = 20;

function SectionHeading({ title, count }: { title: string; count: number }) {
  const capped = count >= MAX_PER_TYPE;
  return (
    <h2 className="mb-3 font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
      {title} ({capped ? `${count}+` : count})
      {capped && (
        <span className="ml-2 font-body text-[10px] normal-case tracking-normal text-on-surface-variant">
          — showing first {MAX_PER_TYPE}, refine your search for more
        </span>
      )}
    </h2>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full bg-surface-container-highest px-2 py-0.5 font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
      {children}
    </span>
  );
}

export default function SearchResults() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get('q') ?? '';

  const {
    data: results,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['search', q],
    queryFn: () => globalSearch(q),
    enabled: q.length > 0,
  });

  const hasResults =
    results &&
    (results.creators.length > 0 ||
      results.arcs.length > 0 ||
      results.artifacts.length > 0 ||
      results.works.length > 0 ||
      results.collections.length > 0);

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">Search Results</h1>
        {q && (
          <p className="mt-2 font-body text-base text-on-surface-variant">
            Results for &ldquo;{q}&rdquo;
          </p>
        )}
      </header>

      {!q && (
        <div className="flex flex-col items-center gap-4 py-20">
          <span className="material-symbols-outlined text-5xl text-on-surface-variant">search</span>
          <p className="font-body text-sm text-on-surface-variant">
            Enter a search term to find items in your library.
          </p>
        </div>
      )}

      {isLoading && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-xl bg-surface-container-low" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-2xl bg-error-container p-6 text-on-error-container">
          <p className="font-body text-sm">
            Search failed. {error instanceof Error ? error.message : 'Unknown error.'}
          </p>
        </div>
      )}

      {!isLoading && !isError && q && !hasResults && (
        <div className="flex flex-col items-center gap-4 py-20">
          <span className="material-symbols-outlined text-5xl text-on-surface-variant">
            search_off
          </span>
          <p className="font-body text-sm text-on-surface-variant">
            No results found for &ldquo;{q}&rdquo;. Try a different search term.
          </p>
        </div>
      )}

      {results && hasResults && (
        <div className="flex flex-col gap-10">
          {/* Creators */}
          {results.creators.length > 0 && (
            <section>
              <SectionHeading title="Creators" count={results.creators.length} />
              <div className="flex flex-col gap-1">
                {results.creators.map((c) => (
                  <Link
                    key={c.creator_id}
                    to={`/creators/${c.creator_id}`}
                    className="flex items-center gap-3 rounded-xl px-4 py-3 font-body text-sm text-on-surface hover:bg-surface-container-low"
                  >
                    <span className="material-symbols-outlined text-secondary text-lg">person</span>
                    {c.display_name}
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Story Arcs */}
          {results.arcs.length > 0 && (
            <section>
              <SectionHeading title="Story Arcs" count={results.arcs.length} />
              <div className="flex flex-col gap-1">
                {results.arcs.map((a) => (
                  <Link
                    key={a.arc_id}
                    to={`/arcs/${a.arc_id}`}
                    className="flex items-center gap-3 rounded-xl px-4 py-3 font-body text-sm text-on-surface hover:bg-surface-container-low"
                  >
                    <span className="material-symbols-outlined text-secondary text-lg">
                      timeline
                    </span>
                    <span className="flex-1">{a.name}</span>
                    {a.total_parts != null && <Badge>{a.total_parts} parts</Badge>}
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Artifacts */}
          {results.artifacts.length > 0 && (
            <section>
              <SectionHeading title="Artifacts" count={results.artifacts.length} />
              <div className="flex flex-col gap-2">
                {results.artifacts.map((a) => (
                  <Link
                    key={a.artifact_id}
                    to={`/artifacts/${a.artifact_id}`}
                    className="group flex items-center gap-4 rounded-xl pr-4 transition-colors hover:bg-surface-container-low"
                  >
                    <div className="w-14 overflow-hidden rounded-l-xl shrink-0 shadow-sm leading-[0]">
                      <CoverImage
                        artifactId={a.artifact_id}
                        title={a.title}
                        className="w-full h-auto aspect-[2/3] object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    </div>
                    <div className="flex-1 min-w-0 py-2">
                      <h4 className="font-headline text-sm text-on-surface font-semibold truncate">
                        {a.title}
                      </h4>
                      {a.publisher && (
                        <p className="font-body text-xs text-on-surface-variant truncate mt-0.5">
                          {a.publisher}
                        </p>
                      )}
                    </div>
                    <div className="shrink-0 hidden sm:block">
                      <Badge>{a.format}</Badge>
                    </div>
                    <span className="material-symbols-outlined text-outline-variant text-[18px] opacity-0 group-hover:opacity-100 transition-opacity">
                      chevron_right
                    </span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Works */}
          {results.works.length > 0 && (
            <section>
              <SectionHeading title="Works" count={results.works.length} />
              <div className="flex flex-col gap-1">
                {results.works.map((w) => (
                  <Link
                    key={w.work_id}
                    to={`/works/${w.work_id}`}
                    className="flex items-center gap-3 rounded-xl px-4 py-3 font-body text-sm text-on-surface hover:bg-surface-container-low"
                  >
                    <span className="material-symbols-outlined text-secondary text-lg">
                      menu_book
                    </span>
                    <span className="flex-1">{w.title}</span>
                    <Badge>{w.work_type}</Badge>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Collections */}
          {results.collections.length > 0 && (
            <section>
              <SectionHeading title="Collections" count={results.collections.length} />
              <div className="flex flex-col gap-1">
                {results.collections.map((c) => (
                  <Link
                    key={c.collection_id}
                    to={`/collections/${c.collection_id}`}
                    className="flex items-center gap-3 rounded-xl px-4 py-3 font-body text-sm text-on-surface hover:bg-surface-container-low"
                  >
                    <span className="material-symbols-outlined text-secondary text-lg">
                      folder_special
                    </span>
                    <span className="flex-1">{c.name}</span>
                    <Badge>{c.collection_type}</Badge>
                  </Link>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
