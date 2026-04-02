import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getWork } from '../api/works';
import { getCollection } from '../api/collections';
import { getArc } from '../api/arcs';
import { formatRoleLabel } from '../lib/utils';
import { useProfile } from '../hooks/useProfile';
import { listActivity } from '../api/activity';
import FormatBadge from '../components/shared/FormatBadge';
import CoverImage from '../components/shared/CoverImage';
import ReadingStatusBadge from '../components/shared/ReadingStatusBadge';

export default function WorkDetail() {
  const { workId: work_id } = useParams<{ workId: string }>();
  const { profile } = useProfile();

  const {
    data: work,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['work', work_id],
    queryFn: () => getWork(work_id!),
    enabled: !!work_id,
  });

  // Fetch reading status from activity log for the current profile
  const { data: activities } = useQuery({
    queryKey: ['activity', work_id, profile],
    queryFn: () =>
      listActivity({ work_id: work_id!, profile: profile ?? undefined }),
    enabled: !!work_id && !!profile,
  });

  // Derive current reading status from most recent activity
  const latestStatus = activities
    ?.filter((a) => a.event_type === 'status_change')
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    )[0]?.event_value;

  // --- Loading ---
  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
        <div className="mx-auto max-w-4xl space-y-8">
          <div className="h-14 w-3/4 animate-pulse rounded-xl bg-surface-container-low" />
          <div className="h-8 w-1/3 animate-pulse rounded-lg bg-surface-container-low" />
          <div className="grid grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-32 animate-pulse rounded-2xl bg-surface-container-low"
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError || !work) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <div className="text-center">
          <h2 className="font-headline text-3xl text-primary">
            Work not found
          </h2>
          <p className="mt-2 font-body text-on-surface-variant">
            This work may have been removed or the link is invalid.
          </p>
          <Link
            to="/"
            className="mt-6 inline-block rounded-full bg-primary px-6 py-2.5 font-label text-sm font-bold text-on-primary"
          >
            Back to Library
          </Link>
        </div>
      </div>
    );
  }

  // Group creators by role
  const creatorsByRole = work.creators.reduce<
    Record<string, typeof work.creators>
  >((acc, cr) => {
    const role = cr.role;
    if (!acc[role]) acc[role] = [];
    acc[role].push(cr);
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <div className="mx-auto max-w-4xl space-y-10">
        {/* Hero */}
        <header className="space-y-4">
          <h1 className="font-headline text-5xl text-primary leading-tight">
            {work.title}
          </h1>

          <div className="flex flex-wrap items-center gap-3">
            <FormatBadge format={work.work_type} />
            {work.original_publication_year && (
              <span className="font-body text-sm text-on-surface-variant">
                {work.original_publication_year}
              </span>
            )}
            {latestStatus && (
              <ReadingStatusBadge status={latestStatus} />
            )}
          </div>
        </header>

        {/* Creators */}
        {Object.keys(creatorsByRole).length > 0 && (
          <section>
            <SectionLabel>Creators</SectionLabel>
            <div className="mt-3 space-y-1">
              {Object.entries(creatorsByRole).map(([role, creators]) => (
                <p key={role} className="font-body text-base text-on-surface">
                  {formatRoleLabel(role)}{' '}
                  {creators.map((cr, i) => (
                    <span key={cr.id}>
                      {i > 0 && ', '}
                      <Link
                        to={`/creators/${cr.creator_id}`}
                        className="text-primary underline-offset-2 hover:underline"
                      >
                        {cr.creator?.display_name ?? 'Unknown'}
                      </Link>
                    </span>
                  ))}
                </p>
              ))}
            </div>
          </section>
        )}

        {/* Series Position */}
        {work.work_collections.length > 0 && (
          <section>
            <SectionLabel>Series</SectionLabel>
            <div className="mt-3 space-y-3">
              {work.work_collections.map((wc) => (
                <CollectionPosition
                  key={wc.id}
                  collectionId={wc.collection_id}
                  sequenceNumber={wc.sequence_number}
                  collectionName={wc.collection?.name}
                  workId={work.work_id}
                />
              ))}
            </div>
          </section>
        )}

        {/* Arc Position */}
        {work.arc_memberships.length > 0 && (
          <section>
            <SectionLabel>Story Arcs</SectionLabel>
            <div className="mt-3 space-y-3">
              {work.arc_memberships.map((am) => (
                <ArcPosition
                  key={am.id}
                  arcId={am.arc_id}
                  arcPosition={am.arc_position}
                  arcName={am.arc?.name}
                  totalParts={am.arc?.total_parts}
                  workId={work.work_id}
                />
              ))}
            </div>
          </section>
        )}

        {/* Volume Run */}
        {work.volume_run && (
          <section>
            <SectionLabel>Original Publication</SectionLabel>
            <p className="mt-2 font-body text-base text-on-surface">
              Originally published in{' '}
              <span className="font-semibold">{work.volume_run.name}</span>
              {work.issue_number && ` #${work.issue_number}`}
            </p>
          </section>
        )}

        {/* In Your Library */}
        {work.artifact_works.length > 0 && (
          <section>
            <SectionLabel>In Your Library</SectionLabel>
            <div className="mt-3 space-y-3">
              {work.artifact_works.map((aw) => {
                if (!aw.artifact) return null;
                const art = aw.artifact;
                return (
                  <Link
                    key={aw.id}
                    to={`/artifacts/${aw.artifact_id}`}
                    className="flex items-center gap-4 rounded-2xl bg-surface-container-low p-4 transition-colors hover:bg-surface-container"
                  >
                    <CoverImage
                      artifactId={aw.artifact_id}
                      title={art.title}
                      className="h-20 w-14 shrink-0 rounded-lg"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-headline text-lg text-primary">
                        {art.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <FormatBadge format={art.format} />
                        {art.publisher && (
                          <span className="font-body text-xs text-on-surface-variant">
                            {art.publisher}
                          </span>
                        )}
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </section>
        )}

        {/* External Links */}
        {(work.goodreads_url || work.comicvine_url) && (
          <section>
            <SectionLabel>External Links</SectionLabel>
            <div className="mt-3 flex flex-wrap gap-3">
              {work.goodreads_url && (
                <a
                  href={work.goodreads_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-full bg-surface-container-low px-5 py-2.5 font-label text-sm font-bold text-primary transition-colors hover:bg-surface-container"
                >
                  Goodreads
                  <ExternalLinkIcon />
                </a>
              )}
              {work.comicvine_url && (
                <a
                  href={work.comicvine_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-full bg-surface-container-low px-5 py-2.5 font-label text-sm font-bold text-primary transition-colors hover:bg-surface-container"
                >
                  ComicVine
                  <ExternalLinkIcon />
                </a>
              )}
            </div>
          </section>
        )}

        {/* Subject Tags */}
        {work.subject_tags && work.subject_tags.length > 0 && (
          <section>
            <SectionLabel>Subjects</SectionLabel>
            <div className="mt-3 flex flex-wrap gap-2">
              {work.subject_tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-surface-container-low px-3 py-1 font-label text-xs text-on-surface-variant"
                >
                  {tag}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Notes */}
        {work.notes && (
          <section>
            <SectionLabel>Notes</SectionLabel>
            <p className="mt-2 whitespace-pre-wrap font-body text-base text-on-surface-variant">
              {work.notes}
            </p>
          </section>
        )}
      </div>
    </div>
  );
}

// --- Helper components ---

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
      {children}
    </h2>
  );
}

function ExternalLinkIcon() {
  return (
    <svg
      className="h-3.5 w-3.5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3"
      />
    </svg>
  );
}

/** Fetches collection detail to show prev/next navigation within a series. */
function CollectionPosition({
  collectionId,
  sequenceNumber,
  collectionName,
  workId,
}: {
  collectionId: string;
  sequenceNumber?: number | null;
  collectionName?: string;
  workId: string;
}) {
  const { data: collection } = useQuery({
    queryKey: ['collection', collectionId],
    queryFn: () => getCollection(collectionId),
  });

  const totalWorks = collection?.works.length ?? 0;
  const sortedWorks = [...(collection?.works ?? [])].sort(
    (a, b) => (a.sequence_number ?? 0) - (b.sequence_number ?? 0),
  );
  const currentIdx = sortedWorks.findIndex((w) => w.work.work_id === workId);
  const prevWork = currentIdx > 0 ? sortedWorks[currentIdx - 1] : null;
  const nextWork =
    currentIdx >= 0 && currentIdx < sortedWorks.length - 1
      ? sortedWorks[currentIdx + 1]
      : null;

  return (
    <div className="rounded-2xl bg-surface-container-low p-5">
      <p className="font-body text-base text-on-surface">
        {sequenceNumber != null ? (
          <>
            Book {sequenceNumber} of {totalWorks || '?'} in{' '}
          </>
        ) : (
          <>Part of </>
        )}
        <Link
          to={`/collections/${collectionId}`}
          className="font-semibold text-primary underline-offset-2 hover:underline"
        >
          {collectionName ?? 'Unknown Collection'}
        </Link>
      </p>

      {(prevWork || nextWork) && (
        <div className="mt-3 flex items-center gap-4">
          {prevWork ? (
            <Link
              to={`/works/${prevWork.work.work_id}`}
              className="flex items-center gap-1 font-label text-xs font-bold text-primary"
            >
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              {prevWork.work.title}
            </Link>
          ) : (
            <span />
          )}
          {nextWork && (
            <Link
              to={`/works/${nextWork.work.work_id}`}
              className="ml-auto flex items-center gap-1 font-label text-xs font-bold text-primary"
            >
              {nextWork.work.title}
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

/** Fetches arc detail to show prev/next navigation within an arc. */
function ArcPosition({
  arcId,
  arcPosition,
  arcName,
  totalParts,
  workId,
}: {
  arcId: string;
  arcPosition?: number | null;
  arcName?: string;
  totalParts?: number | null;
  workId: string;
}) {
  const { data: arc } = useQuery({
    queryKey: ['arc', arcId],
    queryFn: () => getArc(arcId),
  });

  const sortedWorks = [...(arc?.works ?? [])].sort(
    (a, b) => (a.arc_position ?? 0) - (b.arc_position ?? 0),
  );
  const currentIdx = sortedWorks.findIndex((w) => w.work.work_id === workId);
  const prevWork = currentIdx > 0 ? sortedWorks[currentIdx - 1] : null;
  const nextWork =
    currentIdx >= 0 && currentIdx < sortedWorks.length - 1
      ? sortedWorks[currentIdx + 1]
      : null;

  const displayTotal = totalParts ?? arc?.works.length ?? '?';

  return (
    <div className="rounded-2xl bg-surface-container-low p-5">
      <p className="font-body text-base text-on-surface">
        {arcPosition != null ? (
          <>
            Part {arcPosition} of {displayTotal} in{' '}
          </>
        ) : (
          <>Part of </>
        )}
        <Link
          to={`/arcs/${arcId}`}
          className="font-semibold text-primary underline-offset-2 hover:underline"
        >
          {arcName ?? 'Unknown Arc'}
        </Link>
      </p>

      {(prevWork || nextWork) && (
        <div className="mt-3 flex items-center gap-4">
          {prevWork ? (
            <Link
              to={`/works/${prevWork.work.work_id}`}
              className="flex items-center gap-1 font-label text-xs font-bold text-primary"
            >
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              {prevWork.work.title}
            </Link>
          ) : (
            <span />
          )}
          {nextWork && (
            <Link
              to={`/works/${nextWork.work.work_id}`}
              className="ml-auto flex items-center gap-1 font-label text-xs font-bold text-primary"
            >
              {nextWork.work.title}
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
