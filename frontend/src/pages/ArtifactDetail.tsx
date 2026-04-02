import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getArtifact, updateArtifact, deleteArtifact, coverUrl } from '../api/artifacts';
import type { ArtifactUpdate } from '../types';
import { ARTIFACT_FORMATS, LOCATIONS } from '../types';
import { cn, formatRoleLabel } from '../lib/utils';
import CoverImage from '../components/shared/CoverImage';
import FormatBadge from '../components/shared/FormatBadge';
import DeleteConfirmDialog from '../components/shared/DeleteConfirmDialog';

export default function ArtifactDetail() {
  const { artifactId: artifact_id } = useParams<{ artifactId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<ArtifactUpdate>({});
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [dangerExpanded, setDangerExpanded] = useState(false);

  const {
    data: artifact,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['artifact', artifact_id],
    queryFn: () => getArtifact(artifact_id!),
    enabled: !!artifact_id,
  });

  const updateMutation = useMutation({
    mutationFn: (data: ArtifactUpdate) => updateArtifact(artifact_id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifact', artifact_id] });
      queryClient.invalidateQueries({ queryKey: ['artifacts'] });
      setIsEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteArtifact(artifact_id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifacts'] });
      navigate('/');
    },
  });

  const pirateMutation = useMutation({
    mutationFn: (is_pirated: boolean) =>
      updateArtifact(artifact_id!, { is_pirated }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifact', artifact_id] });
    },
  });

  function startEditing() {
    if (!artifact) return;
    setEditData({
      title: artifact.title,
      format: artifact.format,
      publisher: artifact.publisher,
      edition_year: artifact.edition_year,
      isbn_or_upc: artifact.isbn_or_upc,
      is_reprint: artifact.is_reprint,
      original_publisher: artifact.original_publisher,
      owner: artifact.owner,
      size: artifact.size,
      main_genre: artifact.main_genre,
      sous_genre: artifact.sous_genre,
      goodreads_url: artifact.goodreads_url,
      notes: artifact.notes,
    });
    setIsEditing(true);
  }

  function cancelEditing() {
    setIsEditing(false);
    setEditData({});
  }

  function handleSave() {
    updateMutation.mutate(editData);
  }

  // --- Loading skeleton ---
  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
        <div className="mx-auto max-w-5xl">
          {/* Hero skeleton */}
          <div className="relative mb-12 flex flex-col gap-8 overflow-hidden rounded-3xl bg-surface-container-low p-8 md:flex-row md:items-end">
            <div className="h-[480px] w-80 animate-pulse rounded-2xl bg-surface-container" />
            <div className="flex-1 space-y-4">
              <div className="h-12 w-3/4 animate-pulse rounded-xl bg-surface-container" />
              <div className="h-6 w-1/2 animate-pulse rounded-lg bg-surface-container" />
              <div className="h-8 w-24 animate-pulse rounded-full bg-surface-container" />
            </div>
          </div>
          {/* Metadata skeleton */}
          <div className="grid grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-24 animate-pulse rounded-2xl bg-surface-container-low"
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError || !artifact) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <div className="text-center">
          <h2 className="font-headline text-3xl text-primary">
            Artifact not found
          </h2>
          <p className="mt-2 font-body text-on-surface-variant">
            This artifact may have been removed or the link is invalid.
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

  const sortedWorks = [...artifact.artifact_works].sort(
    (a, b) => a.position - b.position,
  );

  return (
    <div className="min-h-screen bg-surface">
      {/* Hero Section with blurred cover background */}
      <section className="relative overflow-hidden">
        {/* Blurred background */}
        <div className="absolute inset-0 z-0">
          {artifact.cover_image_path && (
            <img
              src={coverUrl(artifact.artifact_id)}
              alt=""
              aria-hidden
              className="h-full w-full scale-110 object-cover blur-3xl opacity-30"
            />
          )}
          <div className="absolute inset-0 bg-surface/70" />
        </div>

        <div className="relative z-10 mx-auto flex max-w-5xl flex-col gap-8 px-6 py-12 md:flex-row md:items-end lg:px-12">
          {/* Cover */}
          <div className="shrink-0">
            <CoverImage
              artifactId={artifact.artifact_id}
              title={artifact.title}
              className="w-80 aspect-[2/3] rounded-2xl shadow-2xl"
            />
          </div>

          {/* Title & metadata */}
          <div className="flex-1 space-y-4 pb-4">
            {isEditing ? (
              <input
                type="text"
                value={editData.title ?? ''}
                onChange={(e) =>
                  setEditData((d) => ({ ...d, title: e.target.value }))
                }
                className="w-full rounded-xl bg-surface-container-low px-4 py-3 font-headline text-5xl text-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            ) : (
              <h1 className="font-headline text-7xl text-primary leading-tight">
                {artifact.title}
              </h1>
            )}

            <div className="flex flex-wrap items-center gap-3">
              {isEditing ? (
                <select
                  value={editData.format ?? artifact.format}
                  onChange={(e) =>
                    setEditData((d) => ({ ...d, format: e.target.value }))
                  }
                  className="rounded-xl bg-surface-container-low px-3 py-2 font-body text-sm text-on-surface focus:outline-none"
                >
                  {ARTIFACT_FORMATS.map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
              ) : (
                <FormatBadge format={artifact.format} />
              )}

              {artifact.edition_year && (
                <span className="font-body text-sm text-on-surface-variant">
                  {artifact.edition_year}
                </span>
              )}
            </div>

            {isEditing ? (
              <input
                type="text"
                value={editData.publisher ?? ''}
                placeholder="Publisher"
                onChange={(e) =>
                  setEditData((d) => ({ ...d, publisher: e.target.value }))
                }
                className="rounded-xl bg-surface-container-low px-4 py-2 font-headline italic text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            ) : (
              artifact.publisher && (
                <p className="font-headline text-lg italic text-on-surface-variant">
                  {artifact.publisher}
                </p>
              )
            )}

            {/* Creators */}
            {artifact.creators.length > 0 && (
              <div className="flex flex-wrap gap-x-4 gap-y-1">
                {artifact.creators.map((cr) => (
                  <span key={cr.id} className="font-body text-sm text-on-surface-variant">
                    {formatRoleLabel(cr.role)}{' '}
                    <Link
                      to={`/creators/${cr.creator_id}`}
                      className="text-primary underline-offset-2 hover:underline"
                    >
                      {cr.creator?.display_name ?? 'Unknown'}
                    </Link>
                  </span>
                ))}
              </div>
            )}

            {/* Edit / Save / Cancel buttons */}
            <div className="flex items-center gap-3 pt-2">
              {isEditing ? (
                <>
                  <button
                    onClick={handleSave}
                    disabled={updateMutation.isPending}
                    className="rounded-full bg-primary px-6 py-2.5 font-label text-sm font-bold text-on-primary transition-opacity disabled:opacity-50"
                  >
                    {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    onClick={cancelEditing}
                    className="rounded-full bg-surface-container px-6 py-2.5 font-label text-sm font-bold text-on-surface-variant"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={startEditing}
                  className="rounded-full bg-surface-container px-6 py-2.5 font-label text-sm font-bold text-on-surface-variant transition-colors hover:bg-surface-container-high"
                >
                  Edit Archival Record
                </button>
              )}
            </div>

            {updateMutation.isError && (
              <p className="font-body text-sm text-error">
                Failed to save changes. Please try again.
              </p>
            )}
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-5xl space-y-10 px-6 py-10 lg:px-12">
        {/* Metadata Bento Grid */}
        <section className="grid grid-cols-2 gap-4">
          <MetadataCell
            label="Location"
            value={
              isEditing ? (
                <select
                  value={editData.owner ?? artifact.owner ?? ''}
                  onChange={(e) =>
                    setEditData((d) => ({ ...d, owner: e.target.value }))
                  }
                  className="mt-1 rounded-lg bg-surface-container-low px-2 py-1 font-headline text-xl text-primary focus:outline-none"
                >
                  <option value="">--</option>
                  {LOCATIONS.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
              ) : (
                artifact.copies[0]?.location ?? 'Not set'
              )
            }
          />
          <MetadataCell
            label="Condition"
            value={artifact.copies[0]?.condition ?? 'Unknown'}
          />
          <MetadataCell
            label="Size"
            value={
              isEditing ? (
                <input
                  type="text"
                  value={editData.size ?? ''}
                  placeholder="e.g. 6x9 in"
                  onChange={(e) =>
                    setEditData((d) => ({ ...d, size: e.target.value }))
                  }
                  className="mt-1 rounded-lg bg-surface-container-low px-2 py-1 font-headline text-xl text-primary focus:outline-none"
                />
              ) : (
                artifact.size ?? 'Not recorded'
              )
            }
          />
          <MetadataCell
            label="Owner"
            value={artifact.owner ?? 'Unknown'}
          />
        </section>

        {/* Reprint Lineage */}
        {artifact.is_reprint && artifact.volume_run && (
          <section>
            <SectionLabel>Reprint Lineage</SectionLabel>
            <p className="mt-2 font-body text-base text-on-surface">
              Reprints:{' '}
              <Link
                to={`/volume-runs/${artifact.volume_run.volume_run_id}`}
                className="text-primary underline-offset-2 hover:underline"
              >
                {artifact.volume_run.name}
              </Link>
              {artifact.issue_number && ` #${artifact.issue_number}`}
              {artifact.original_publisher &&
                ` (${artifact.original_publisher})`}
            </p>
          </section>
        )}

        {/* What's Inside */}
        {sortedWorks.length > 0 && (
          <section>
            <SectionLabel>What's Inside</SectionLabel>
            <ol className="mt-3 space-y-2">
              {sortedWorks.map((aw, idx) => (
                <li
                  key={aw.id}
                  className="flex items-baseline gap-3 font-body text-base"
                >
                  <span className="shrink-0 font-label text-xs text-on-surface-variant">
                    {idx + 1}.
                  </span>
                  <Link
                    to={`/works/${aw.work_id}`}
                    className="text-primary underline-offset-2 hover:underline"
                  >
                    {aw.work?.title ?? 'Untitled Work'}
                  </Link>
                  {aw.is_partial && (
                    <span className="rounded-full bg-tertiary-fixed px-2 py-0.5 font-label text-[10px] font-bold uppercase tracking-widest text-on-tertiary-fixed">
                      Partial
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </section>
        )}

        {/* Copies */}
        {artifact.copies.length > 0 && (
          <section>
            <SectionLabel>Copies</SectionLabel>
            <div className="mt-3 space-y-3">
              {artifact.copies.map((copy) => (
                <div
                  key={copy.copy_id}
                  className="rounded-2xl bg-surface-container-low p-4"
                >
                  <div className="flex items-baseline justify-between">
                    <span className="font-headline text-lg text-primary">
                      Copy #{copy.copy_number}
                    </span>
                    {copy.condition && (
                      <span className="font-label text-xs text-on-surface-variant">
                        {copy.condition}
                      </span>
                    )}
                  </div>
                  {copy.location && (
                    <p className="mt-1 font-body text-sm text-on-surface-variant">
                      {copy.location}
                    </p>
                  )}
                  {copy.borrower_name && (
                    <p className="mt-1 font-body text-sm text-tertiary-fixed">
                      Lent to {copy.borrower_name}
                      {copy.lent_date && ` on ${copy.lent_date}`}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Notes */}
        {(artifact.notes || isEditing) && (
          <section>
            <SectionLabel>Notes</SectionLabel>
            {isEditing ? (
              <textarea
                value={editData.notes ?? ''}
                onChange={(e) =>
                  setEditData((d) => ({ ...d, notes: e.target.value }))
                }
                rows={4}
                className="mt-2 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            ) : (
              <p className="mt-2 whitespace-pre-wrap font-body text-base text-on-surface-variant">
                {artifact.notes}
              </p>
            )}
          </section>
        )}

        {/* Genre & ISBN */}
        {(artifact.main_genre || artifact.isbn_or_upc || artifact.goodreads_url) && (
          <section>
            <SectionLabel>Additional Info</SectionLabel>
            <div className="mt-3 space-y-1 font-body text-sm text-on-surface-variant">
              {artifact.main_genre && (
                <p>
                  Genre: {artifact.main_genre}
                  {artifact.sous_genre && ` / ${artifact.sous_genre}`}
                </p>
              )}
              {artifact.isbn_or_upc && <p>ISBN/UPC: {artifact.isbn_or_upc}</p>}
              {artifact.goodreads_url && (
                <p>
                  <a
                    href={artifact.goodreads_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary underline-offset-2 hover:underline"
                  >
                    View on Goodreads
                  </a>
                </p>
              )}
            </div>
          </section>
        )}

        {/* Danger Zone */}
        <section>
          <button
            onClick={() => setDangerExpanded(!dangerExpanded)}
            className="flex w-full items-center gap-2 font-label text-[10px] font-bold uppercase tracking-widest text-error"
          >
            <svg
              className={cn(
                'h-4 w-4 transition-transform',
                dangerExpanded && 'rotate-90',
              )}
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
            Danger Zone
          </button>

          {dangerExpanded && (
            <div className="mt-4 space-y-4 rounded-2xl bg-error-container/20 p-6">
              {/* Pirated toggle: only show when is_pirated is true */}
              {artifact.is_pirated && (
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-body text-sm font-semibold text-on-surface">
                      Pirated Copy
                    </p>
                    <p className="font-body text-xs text-on-surface-variant">
                      This artifact is flagged as a pirated copy.
                    </p>
                  </div>
                  <button
                    onClick={() => pirateMutation.mutate(false)}
                    disabled={pirateMutation.isPending}
                    className="rounded-full bg-error px-4 py-2 font-label text-xs font-bold text-on-error disabled:opacity-50"
                  >
                    Remove Flag
                  </button>
                </div>
              )}

              {/* Delete */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-body text-sm font-semibold text-on-surface">
                    Delete Artifact
                  </p>
                  <p className="font-body text-xs text-on-surface-variant">
                    Permanently remove this artifact and all its data.
                  </p>
                </div>
                <button
                  onClick={() => setShowDeleteDialog(true)}
                  className="rounded-full bg-error px-4 py-2 font-label text-xs font-bold text-on-error"
                >
                  Delete
                </button>
              </div>
            </div>
          )}
        </section>
      </div>

      {/* Delete Confirmation Dialog */}
      <DeleteConfirmDialog
        isOpen={showDeleteDialog}
        title={artifact.title}
        onCancel={() => setShowDeleteDialog(false)}
        onConfirm={() => deleteMutation.mutate()}
      />
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

function MetadataCell({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl bg-surface-container-low p-5">
      <span className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
        {label}
      </span>
      {typeof value === 'string' ? (
        <p className="mt-1 font-headline text-2xl text-primary">{value}</p>
      ) : (
        <div className="mt-1">{value}</div>
      )}
    </div>
  );
}
