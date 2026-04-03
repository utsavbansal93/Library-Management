import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getWork, updateWork } from '../api/works';
import { getCollection } from '../api/collections';
import { getArc } from '../api/arcs';
import { logActivity } from '../api/activity';
import { formatRoleLabel } from '../lib/utils';
import { useProfile } from '../hooks/useProfile';
import { listActivity } from '../api/activity';
import { useToast } from '../hooks/useToast';
import type { WorkUpdate, ActivityCreate } from '../types';
import { WORK_TYPES } from '../types';
import FormatBadge from '../components/shared/FormatBadge';
import CoverImage from '../components/shared/CoverImage';
import ReadingStatusBadge from '../components/shared/ReadingStatusBadge';
import BackButton from '../components/shared/BackButton';
import TagInput from '../components/shared/TagInput';

export default function WorkDetail() {
  const { workId: work_id } = useParams<{ workId: string }>();
  const { profile } = useProfile();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<WorkUpdate>({});

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
  const STATUS_EVENT_TYPES = ['Started_Reading', 'Finished_Reading', 'Abandoned/DNF'];
  const latestStatusEntry = activities
    ?.filter((a) => STATUS_EVENT_TYPES.includes(a.event_type))
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    )[0];
  const latestStatus = latestStatusEntry?.event_type;

  const updateMutation = useMutation({
    mutationFn: (data: WorkUpdate) => updateWork(work_id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work', work_id] });
      setIsEditing(false);
      showToast('Work saved successfully');
    },
    onError: () => showToast('Failed to save changes.'),
  });

  const activityMutation = useMutation({
    mutationFn: (data: ActivityCreate) => logActivity(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity', work_id, profile] });
      showToast('Activity logged');
    },
    onError: () => showToast('Failed to log activity.'),
  });

  function startEditing() {
    if (!work) return;
    setEditData({
      title: work.title,
      work_type: work.work_type,
      original_publication_year: work.original_publication_year,
      subject_tags: work.subject_tags ?? [],
      goodreads_url: work.goodreads_url,
      comicvine_url: work.comicvine_url,
      notes: work.notes,
    });
    setIsEditing(true);
  }

  function logStatusEvent(eventType: string) {
    if (!profile || !work_id) return;
    activityMutation.mutate({
      user_profile: profile,
      work_id: work_id,
      event_type: eventType,
      timestamp: new Date().toISOString(),
    });
  }

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
    <div className="min-h-screen bg-surface px-6 py-8 lg:px-8">
      <div className="mx-auto max-w-4xl space-y-8">
        <BackButton />
        {/* Hero */}
        <header className="space-y-4">
          {isEditing ? (
            <input
              type="text"
              value={editData.title ?? ''}
              onChange={(e) => setEditData((d) => ({ ...d, title: e.target.value }))}
              className="w-full bg-transparent font-headline text-4xl md:text-5xl text-primary leading-tight focus:outline-none border-b border-primary/30"
            />
          ) : (
            <h1 className="font-headline text-4xl md:text-5xl text-primary leading-tight">
              {work.title}
            </h1>
          )}

          <div className="flex flex-wrap items-center gap-3">
            {isEditing ? (
              <select
                value={editData.work_type ?? work.work_type}
                onChange={(e) => setEditData((d) => ({ ...d, work_type: e.target.value }))}
                className="rounded-xl bg-surface-container-low px-3 py-2 font-body text-sm text-on-surface focus:outline-none"
              >
                {WORK_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            ) : (
              <FormatBadge format={work.work_type} />
            )}
            {isEditing ? (
              <input
                type="number"
                value={editData.original_publication_year ?? ''}
                onChange={(e) =>
                  setEditData((d) => ({
                    ...d,
                    original_publication_year: e.target.value ? parseInt(e.target.value, 10) : null,
                  }))
                }
                placeholder="Year"
                className="w-24 rounded-xl bg-surface-container-low px-3 py-2 font-body text-sm text-on-surface focus:outline-none"
              />
            ) : (
              work.original_publication_year && (
                <span className="font-body text-sm text-on-surface-variant">
                  {work.original_publication_year}
                </span>
              )
            )}
            {latestStatus && (
              <ReadingStatusBadge status={latestStatus} />
            )}
          </div>

          {/* Edit / Save / Cancel + Activity buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            {isEditing ? (
              <>
                <button
                  onClick={() => updateMutation.mutate(editData)}
                  disabled={updateMutation.isPending}
                  className="rounded-full bg-primary px-6 py-2.5 font-label text-sm font-bold text-on-primary disabled:opacity-50"
                >
                  {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={() => { setIsEditing(false); setEditData({}); }}
                  className="rounded-full bg-surface-container px-6 py-2.5 font-label text-sm font-bold text-on-surface-variant"
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={startEditing}
                  className="rounded-full bg-surface-container px-6 py-2.5 font-label text-sm font-bold text-on-surface-variant hover:bg-surface-container-high"
                >
                  Edit Work
                </button>
                {profile && (
                  <div className="flex items-center gap-2">
                    {latestStatus !== 'Started_Reading' && (
                      <button
                        onClick={() => logStatusEvent('Started_Reading')}
                        disabled={activityMutation.isPending}
                        className="rounded-full bg-tertiary-fixed px-4 py-2 font-label text-xs font-bold text-on-tertiary-fixed disabled:opacity-50"
                      >
                        Start Reading
                      </button>
                    )}
                    {latestStatus === 'Started_Reading' && (
                      <>
                        <button
                          onClick={() => logStatusEvent('Finished_Reading')}
                          disabled={activityMutation.isPending}
                          className="rounded-full bg-primary px-4 py-2 font-label text-xs font-bold text-on-primary disabled:opacity-50"
                        >
                          Finished
                        </button>
                        <button
                          onClick={() => logStatusEvent('Abandoned/DNF')}
                          disabled={activityMutation.isPending}
                          className="rounded-full bg-error px-4 py-2 font-label text-xs font-bold text-on-error disabled:opacity-50"
                        >
                          DNF
                        </button>
                      </>
                    )}
                    {latestStatus === 'Finished_Reading' && (
                      <button
                        onClick={() => logStatusEvent('Started_Reading')}
                        disabled={activityMutation.isPending}
                        className="rounded-full bg-tertiary-fixed px-4 py-2 font-label text-xs font-bold text-on-tertiary-fixed disabled:opacity-50"
                      >
                        Re-read
                      </button>
                    )}
                  </div>
                )}
              </>
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
        {(work.goodreads_url || work.comicvine_url || isEditing) && (
          <section>
            <SectionLabel>External Links</SectionLabel>
            {isEditing ? (
              <div className="mt-3 space-y-2">
                <input
                  type="url"
                  value={editData.goodreads_url ?? ''}
                  onChange={(e) => setEditData((d) => ({ ...d, goodreads_url: e.target.value || null }))}
                  placeholder="Goodreads URL"
                  className="w-full rounded-xl bg-surface-container-low px-4 py-2 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
                <input
                  type="url"
                  value={editData.comicvine_url ?? ''}
                  onChange={(e) => setEditData((d) => ({ ...d, comicvine_url: e.target.value || null }))}
                  placeholder="ComicVine URL"
                  className="w-full rounded-xl bg-surface-container-low px-4 py-2 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
            ) : (
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
            )}
          </section>
        )}

        {/* Subject Tags */}
        {((work.subject_tags && work.subject_tags.length > 0) || isEditing) && (
          <section>
            <SectionLabel>Subjects</SectionLabel>
            {isEditing ? (
              <TagInput
                tags={editData.subject_tags ?? []}
                onChange={(tags) => setEditData((d) => ({ ...d, subject_tags: tags }))}
              />
            ) : (
              <div className="mt-3 flex flex-wrap gap-2">
                {work.subject_tags!.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-surface-container-low px-3 py-1 font-label text-xs text-on-surface-variant"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Notes */}
        {(work.notes || isEditing) && (
          <section>
            <SectionLabel>Notes</SectionLabel>
            {isEditing ? (
              <textarea
                value={editData.notes ?? ''}
                onChange={(e) => setEditData((d) => ({ ...d, notes: e.target.value || null }))}
                rows={4}
                className="mt-2 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            ) : (
              <p className="mt-2 whitespace-pre-wrap font-body text-base text-on-surface-variant">
                {work.notes}
              </p>
            )}
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
            Book {Number.isInteger(sequenceNumber) ? sequenceNumber : sequenceNumber!.toFixed(1)} of {totalWorks || '?'} in{' '}
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
