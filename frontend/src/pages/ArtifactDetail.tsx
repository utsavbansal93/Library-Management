import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getArtifact, updateArtifact, deleteArtifact, coverUrl, updateCopy, createCopy, uploadCover } from '../api/artifacts';
import { useToast } from '../hooks/useToast';
import type { ArtifactUpdate, CopyUpdate } from '../types';
import { ARTIFACT_FORMATS, OWNERS, LOCATIONS } from '../types';
import { cn, formatRoleLabel } from '../lib/utils';
import CoverImage from '../components/shared/CoverImage';
import FormatBadge from '../components/shared/FormatBadge';
import DeleteConfirmDialog from '../components/shared/DeleteConfirmDialog';
import BackButton from '../components/shared/BackButton';

const DIGITAL_FORMATS = ['Kindle', 'Audible'];

function validLocationsForFormat(format: string): string[] {
  if (DIGITAL_FORMATS.includes(format)) {
    return LOCATIONS.filter((l) => l === 'Digital');
  }
  return LOCATIONS.filter((l) => l !== 'Digital');
}

export default function ArtifactDetail() {
  const { artifactId: artifact_id } = useParams<{ artifactId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<ArtifactUpdate>({});
  const [editCopyData, setEditCopyData] = useState<Record<string, CopyUpdate>>({});
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [dangerExpanded, setDangerExpanded] = useState(false);
  
  const titleRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (isEditing && titleRef.current) {
      titleRef.current.style.height = '1px';
      titleRef.current.style.height = titleRef.current.scrollHeight + 'px';
    }
  }, [isEditing, editData.title]);

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
  });

  const copyMutation = useMutation({
    mutationFn: (data: { copyId: string; payload: CopyUpdate }) =>
      updateCopy(artifact_id!, data.copyId, data.payload),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteArtifact(artifact_id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifacts'] });
      showToast('Artifact removed from library');
      navigate('/');
    },
  });

  const addCopyMutation = useMutation({
    mutationFn: () =>
      createCopy(artifact_id!, {
        copy_number: (artifact?.copies.length ?? 0) + 1,
        location: null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifact', artifact_id] });
      showToast('Copy added');
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
      main_genre: artifact.main_genre,
      sous_genre: artifact.sous_genre,
      goodreads_url: artifact.goodreads_url,
      notes: artifact.notes,
    });
    if (artifact.copies.length > 0) {
      const copyMap: Record<string, CopyUpdate> = {};
      artifact.copies.forEach((c) => {
        copyMap[c.copy_id] = { location: c.location, borrower_name: c.borrower_name, lent_date: c.lent_date };
      });
      setEditCopyData(copyMap);
    }
    setIsEditing(true);
  }

  function cancelEditing() {
    setIsEditing(false);
    setEditData({});
    setEditCopyData({});
  }

  async function handleSave() {
    try {
      await updateMutation.mutateAsync(editData);
      for (const [copyId, payload] of Object.entries(editCopyData)) {
        if (Object.keys(payload).length > 0) {
          await copyMutation.mutateAsync({ copyId, payload });
        }
      }
      queryClient.invalidateQueries({ queryKey: ['artifact', artifact_id] });
      queryClient.invalidateQueries({ queryKey: ['artifacts'] });
      setIsEditing(false);
      showToast('Artifact saved successfully');
    } catch (e) {
      console.error(e);
      showToast('Failed to save changes. Please try again.');
    }
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

  // Enriched works for "What's Inside" cards
  const enrichedWorks = [...(artifact.artifact_works_enriched ?? [])].sort(
    (a, b) => a.position - b.position,
  );

  // Common arcs/collections shared by ALL works (for multi-work artifacts)
  const commonArcs =
    enrichedWorks.length > 1
      ? (enrichedWorks[0]?.arc_memberships ?? []).filter((arc) =>
          enrichedWorks.every((w) =>
            w.arc_memberships.some((a) => a.arc_id === arc.arc_id),
          ),
        )
      : [];
  const commonCollections =
    enrichedWorks.length > 1
      ? (enrichedWorks[0]?.collection_memberships ?? []).filter((coll) =>
          enrichedWorks.every((w) =>
            w.collection_memberships.some(
              (c) => c.collection_id === coll.collection_id,
            ),
          ),
        )
      : [];
  const commonArcIds = new Set(commonArcs.map((a) => a.arc_id));
  const commonCollectionIds = new Set(
    commonCollections.map((c) => c.collection_id),
  );

  return (
    <div className="min-h-screen bg-surface">
      <div className="mx-auto max-w-4xl px-6 pt-6 lg:px-8">
        <BackButton />
      </div>
      {isEditing && (
        <div className="bg-primary/10 border-b border-primary/20 px-6 py-2 text-center">
          <span className="font-label text-xs font-bold uppercase tracking-widest text-primary">
            Editing Mode
          </span>
        </div>
      )}
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

        <div className="relative z-10 mx-auto flex max-w-4xl flex-col gap-6 px-6 py-8 md:flex-row md:items-end lg:px-8">
          {/* Cover */}
          <div className="shrink-0 relative">
            <CoverImage
              artifactId={artifact.artifact_id}
              title={artifact.title}
              version={artifact.updated_at}
              className="w-80 aspect-[2/3] rounded-2xl shadow-2xl"
            />
            {isEditing && (
              <CoverDropZone
                artifactId={artifact.artifact_id}
                onUpload={() => {
                  queryClient.invalidateQueries({ queryKey: ['artifact', artifact_id] });
                  showToast('Cover uploaded');
                }}
              />
            )}
          </div>

          {/* Title & metadata */}
          <div className="flex-1 space-y-4 pb-4">
            {isEditing ? (
              <textarea
                ref={titleRef}
                value={editData.title ?? ''}
                rows={1}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = '1px';
                  target.style.height = target.scrollHeight + 'px';
                }}
                onChange={(e) =>
                  setEditData((d) => ({ ...d, title: e.target.value }))
                }
                className="w-full resize-none overflow-hidden bg-transparent font-headline text-4xl leading-tight text-primary md:text-5xl focus:outline-none focus:border-b-2 focus:border-primary/50 border-b border-transparent"
              />
            ) : (
              <h1 className="font-headline text-4xl md:text-5xl text-primary leading-tight">
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
                      className={`text-primary underline-offset-2 hover:underline ${cr.creator?.display_name === 'Various' ? 'italic' : ''}`}
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
                    disabled={updateMutation.isPending || copyMutation.isPending}
                    className="rounded-full bg-primary px-6 py-2.5 font-label text-sm font-bold text-on-primary transition-opacity disabled:opacity-50"
                  >
                    {updateMutation.isPending || copyMutation.isPending ? 'Saving...' : 'Save Changes'}
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

      <div className="mx-auto max-w-4xl space-y-8 px-6 py-8 lg:px-8">
        {/* Metadata Bento Grid */}
        <section className="grid grid-cols-2 gap-4">
          <MetadataCell
            label="Location"
            value={
              isEditing && artifact.copies.length > 0 ? (
                <select
                  value={editCopyData[artifact.copies[0]?.copy_id]?.location ?? artifact.copies[0]?.location ?? ''}
                  onChange={(e) =>
                    setEditCopyData((d) => ({
                      ...d,
                      [artifact.copies[0].copy_id]: {
                        ...d[artifact.copies[0].copy_id],
                        location: e.target.value,
                      },
                    }))
                  }
                  className="mt-1 w-full rounded-lg bg-surface-container-low px-2 py-1 font-headline text-xl text-primary focus:outline-none"
                >
                  <option value="">Not set</option>
                  {validLocationsForFormat(editData.format ?? artifact.format).map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              ) : (
                artifact.copies[0]?.location ?? 'Not set'
              )
            }
          />
          <MetadataCell
            label="Owner"
            value={
              isEditing ? (
                <select
                  value={editData.owner ?? artifact.owner ?? ''}
                  onChange={(e) =>
                    setEditData((d) => ({ ...d, owner: e.target.value }))
                  }
                  className="mt-1 rounded-lg bg-surface-container-low px-2 py-1 font-headline text-xl text-primary focus:outline-none"
                >
                  {OWNERS.map((o) => (
                    <option key={o} value={o}>
                      {o}
                    </option>
                  ))}
                </select>
              ) : (
                artifact.owner ?? 'Unknown'
              )
            }
          />
          <MetadataCell
            label="Edition Year"
            value={
              isEditing ? (
                <input
                  type="number"
                  value={editData.edition_year ?? ''}
                  onChange={(e) =>
                    setEditData((d) => ({
                      ...d,
                      edition_year: e.target.value ? parseInt(e.target.value, 10) : null,
                    }))
                  }
                  placeholder="e.g. 2023"
                  className="mt-1 w-full rounded-lg bg-surface-container-low px-2 py-1 font-headline text-xl text-primary focus:outline-none"
                />
              ) : (
                artifact.edition_year ? String(artifact.edition_year) : 'Not set'
              )
            }
          />
          <MetadataCell
            label="ISBN / UPC"
            value={
              isEditing ? (
                <input
                  type="text"
                  value={editData.isbn_or_upc ?? ''}
                  onChange={(e) =>
                    setEditData((d) => ({ ...d, isbn_or_upc: e.target.value || null }))
                  }
                  placeholder="ISBN or UPC"
                  className="mt-1 w-full rounded-lg bg-surface-container-low px-2 py-1 font-headline text-xl text-primary focus:outline-none"
                />
              ) : (
                artifact.isbn_or_upc ?? 'Not set'
              )
            }
          />
          <MetadataCell
            label="Genre"
            value={
              isEditing ? (
                <div className="mt-1 flex gap-2">
                  <input
                    type="text"
                    value={editData.main_genre ?? ''}
                    onChange={(e) =>
                      setEditData((d) => ({ ...d, main_genre: e.target.value || null }))
                    }
                    placeholder="Main genre"
                    className="w-full rounded-lg bg-surface-container-low px-2 py-1 font-body text-sm text-primary focus:outline-none"
                  />
                  <input
                    type="text"
                    value={editData.sous_genre ?? ''}
                    onChange={(e) =>
                      setEditData((d) => ({ ...d, sous_genre: e.target.value || null }))
                    }
                    placeholder="Sub-genre"
                    className="w-full rounded-lg bg-surface-container-low px-2 py-1 font-body text-sm text-primary focus:outline-none"
                  />
                </div>
              ) : (
                artifact.main_genre
                  ? `${artifact.main_genre}${artifact.sous_genre ? ` / ${artifact.sous_genre}` : ''}`
                  : 'Not set'
              )
            }
          />
          <MetadataCell
            label="Reprint"
            value={
              isEditing ? (
                <label className="mt-1 flex items-center gap-2 font-body text-sm text-on-surface">
                  <input
                    type="checkbox"
                    checked={editData.is_reprint ?? false}
                    onChange={(e) =>
                      setEditData((d) => ({ ...d, is_reprint: e.target.checked }))
                    }
                    className="h-4 w-4 rounded accent-primary"
                  />
                  Is Reprint
                </label>
              ) : (
                artifact.is_reprint ? 'Yes' : 'No'
              )
            }
          />
          {(isEditing || artifact.original_publisher) && (
            <MetadataCell
              label="Original Publisher"
              value={
                isEditing ? (
                  <input
                    type="text"
                    value={editData.original_publisher ?? ''}
                    onChange={(e) =>
                      setEditData((d) => ({ ...d, original_publisher: e.target.value || null }))
                    }
                    placeholder="Original publisher"
                    className="mt-1 w-full rounded-lg bg-surface-container-low px-2 py-1 font-headline text-xl text-primary focus:outline-none"
                  />
                ) : (
                  artifact.original_publisher ?? 'Not set'
                )
              }
            />
          )}
          {(isEditing || artifact.goodreads_url) && (
            <MetadataCell
              label="Goodreads"
              value={
                isEditing ? (
                  <input
                    type="url"
                    value={editData.goodreads_url ?? ''}
                    onChange={(e) =>
                      setEditData((d) => ({ ...d, goodreads_url: e.target.value || null }))
                    }
                    placeholder="Goodreads URL"
                    className="mt-1 w-full rounded-lg bg-surface-container-low px-2 py-1 font-body text-sm text-primary focus:outline-none"
                  />
                ) : (
                  <a
                    href={artifact.goodreads_url!}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary underline-offset-2 hover:underline font-headline text-xl"
                  >
                    View on Goodreads
                  </a>
                )
              }
            />
          )}
        </section>

        {/* Reprint Lineage */}
        {artifact.is_reprint && artifact.volume_run && (
          <section>
            <SectionLabel>Reprint Lineage</SectionLabel>
            <p className="mt-2 font-body text-base text-on-surface">
              Reprints:{' '}
              <Link
                to={`/?volume_run_id=${artifact.volume_run.volume_run_id}`}
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

        {/* Series & Franchises */}
        {((artifact.arc_memberships?.length ?? 0) > 0 ||
          (artifact.collection_memberships?.length ?? 0) > 0) && (
          <section>
            <SectionLabel>Part Of</SectionLabel>
            <div className="mt-3 space-y-2">
              {artifact.arc_memberships?.map((arc) => (
                <Link
                  key={arc.arc_id}
                  to={`/arcs/${arc.arc_id}`}
                  className="flex items-center gap-3 rounded-2xl bg-surface-container-low p-4 transition-colors hover:bg-surface-container"
                >
                  <span className="material-symbols-outlined text-xl text-primary">
                    auto_stories
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-headline text-base text-primary truncate">
                      {arc.name}
                    </p>
                    <p className="font-label text-xs text-on-surface-variant">
                      Story Arc
                      {arc.arc_position != null && (
                        <> · #{arc.arc_position}{arc.total_parts ? ` of ${arc.total_parts}` : ''}</>
                      )}
                      {arc.completion_status && (
                        <> · {arc.completion_status}</>
                      )}
                    </p>
                  </div>
                  <span className="material-symbols-outlined text-sm text-on-surface-variant">
                    chevron_right
                  </span>
                </Link>
              ))}
              {artifact.collection_memberships?.map((coll) => (
                <Link
                  key={coll.collection_id}
                  to={`/collections/${coll.collection_id}`}
                  className="flex items-center gap-3 rounded-2xl bg-surface-container-low p-4 transition-colors hover:bg-surface-container"
                >
                  <span className="material-symbols-outlined text-xl text-primary">
                    collections_bookmark
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-headline text-base text-primary truncate">
                      {coll.name}
                    </p>
                    <p className="font-label text-xs text-on-surface-variant">
                      {coll.collection_type === 'Franchise' ? 'Franchise' : 'Series'}
                      {coll.sequence_number != null && (
                        <> · Book {Number.isInteger(coll.sequence_number) ? coll.sequence_number : coll.sequence_number.toFixed(1)}</>
                      )}
                    </p>
                  </div>
                  <span className="material-symbols-outlined text-sm text-on-surface-variant">
                    chevron_right
                  </span>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* What's Inside — enriched work cards */}
        {enrichedWorks.length > 0 && (
          <section>
            <SectionLabel>What's Inside</SectionLabel>

            {/* Common attributes banner (multi-work only) */}
            {enrichedWorks.length > 1 && commonArcs.length > 0 && (
              <div className="mt-3 rounded-2xl bg-primary/5 border border-primary/10 px-4 py-3">
                <p className="font-body text-xs text-on-surface-variant">
                  All stories are part of{' '}
                  {commonArcs.map((arc, i) => (
                    <span key={arc.arc_id}>
                      {i > 0 && ', '}
                      <Link
                        to={`/arcs/${arc.arc_id}`}
                        className="font-semibold text-primary hover:underline underline-offset-2"
                      >
                        {arc.name}
                      </Link>
                    </span>
                  ))}
                </p>
              </div>
            )}
            {enrichedWorks.length > 1 && commonCollections.length > 0 && (
              <div className={cn(
                'rounded-2xl bg-primary/5 border border-primary/10 px-4 py-3',
                commonArcs.length > 0 ? 'mt-2' : 'mt-3',
              )}>
                <p className="font-body text-xs text-on-surface-variant">
                  Part of the{' '}
                  {commonCollections.map((coll, i) => (
                    <span key={coll.collection_id}>
                      {i > 0 && ', '}
                      <Link
                        to={`/collections/${coll.collection_id}`}
                        className="font-semibold text-primary hover:underline underline-offset-2"
                      >
                        {coll.name}
                      </Link>
                    </span>
                  ))}
                  {' '}series
                </p>
              </div>
            )}

            {/* Per-work cards */}
            <div className="mt-3 space-y-3">
              {enrichedWorks.map((aw) => {
                // Group creators by role
                const roleGroups: Record<string, string[]> = {};
                for (const c of aw.creators) {
                  (roleGroups[c.role] ??= []).push(c.display_name);
                }
                // Non-common arcs/collections for this work
                const uniqueArcs = aw.arc_memberships.filter(
                  (a) => !commonArcIds.has(a.arc_id),
                );
                const uniqueColls = aw.collection_memberships.filter(
                  (c) => !commonCollectionIds.has(c.collection_id),
                );

                return (
                  <div
                    key={aw.id}
                    className="flex gap-4 rounded-2xl bg-surface-container-low p-4"
                  >
                    {/* Cover thumbnail */}
                    <Link to={`/works/${aw.work_id}`} className="shrink-0">
                      <CoverImage
                        workId={aw.work_id}
                        title={aw.title}
                        className="w-16 rounded-lg shadow-sm"
                      />
                    </Link>

                    {/* Details */}
                    <div className="flex-1 min-w-0 space-y-1.5">
                      <div className="flex items-start gap-2">
                        <Link
                          to={`/works/${aw.work_id}`}
                          className="font-headline text-base text-primary hover:underline underline-offset-2 line-clamp-2"
                        >
                          {aw.title}
                        </Link>
                        {aw.is_partial && (
                          <span className="shrink-0 mt-0.5 rounded-full bg-tertiary-fixed px-2 py-0.5 font-label text-[10px] font-bold uppercase tracking-widest text-on-tertiary-fixed">
                            Partial
                          </span>
                        )}
                      </div>

                      {/* Type / Year / Issue */}
                      <p className="font-label text-xs text-on-surface-variant">
                        {aw.work_type}
                        {aw.issue_number && <> · #{aw.issue_number}</>}
                        {aw.original_publication_year && <> · {aw.original_publication_year}</>}
                      </p>

                      {/* Creators by role */}
                      {Object.keys(roleGroups).length > 0 && (
                        <div className="flex flex-wrap gap-x-4 gap-y-0.5">
                          {Object.entries(roleGroups).map(([role, names]) => (
                            <p key={role} className="font-body text-xs text-on-surface-variant">
                              <span className="text-secondary">{formatRoleLabel(role)}:</span>{' '}
                              {names.join(', ')}
                            </p>
                          ))}
                        </div>
                      )}

                      {/* Non-common arcs & collections */}
                      {(uniqueArcs.length > 0 || uniqueColls.length > 0) && (
                        <div className="flex flex-wrap gap-1.5 pt-0.5">
                          {uniqueArcs.map((arc) => (
                            <Link
                              key={arc.arc_id}
                              to={`/arcs/${arc.arc_id}`}
                              className="inline-flex items-center gap-1 rounded-full bg-surface-container-highest px-2 py-0.5 font-label text-[10px] font-bold text-on-surface-variant hover:text-primary transition-colors"
                            >
                              <span className="material-symbols-outlined text-[12px]">auto_stories</span>
                              {arc.name}
                              {arc.arc_position != null && <> #{arc.arc_position}</>}
                            </Link>
                          ))}
                          {uniqueColls.map((coll) => (
                            <Link
                              key={coll.collection_id}
                              to={`/collections/${coll.collection_id}`}
                              className="inline-flex items-center gap-1 rounded-full bg-surface-container-highest px-2 py-0.5 font-label text-[10px] font-bold text-on-surface-variant hover:text-primary transition-colors"
                            >
                              <span className="material-symbols-outlined text-[12px]">collections_bookmark</span>
                              {coll.name}
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Copies */}
        <section>
          <div className="flex items-center justify-between">
            <SectionLabel>Copies</SectionLabel>
            {!isEditing && (
              <button
                onClick={() => addCopyMutation.mutate()}
                disabled={addCopyMutation.isPending}
                className="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 font-label text-xs font-bold text-primary hover:bg-surface-container-low disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[16px]">add</span>
                Add Copy
              </button>
            )}
          </div>
          <div className="mt-3 space-y-3">
            {artifact.copies.map((copy) => (
              <div
                key={copy.copy_id}
                className="rounded-2xl bg-surface-container-low p-4"
              >
                <div className="flex items-center justify-between">
                  <span className="font-headline text-lg text-primary">
                    Copy #{copy.copy_number}
                  </span>
                  {copy.location === 'Lent' && copy.borrower_name && (
                    <span className="rounded-full bg-tertiary-fixed px-2.5 py-0.5 font-label text-[10px] font-bold uppercase tracking-widest text-on-tertiary-fixed">
                      Lent
                    </span>
                  )}
                </div>
                {isEditing ? (
                  <div className="mt-2 space-y-2">
                    <select
                      value={editCopyData[copy.copy_id]?.location ?? copy.location ?? ''}
                      onChange={(e) =>
                        setEditCopyData((d) => ({
                          ...d,
                          [copy.copy_id]: {
                            ...d[copy.copy_id],
                            location: e.target.value,
                          },
                        }))
                      }
                      className="w-full rounded-lg bg-surface-container px-2 py-1 font-body text-sm text-primary focus:outline-none"
                    >
                      <option value="">Not set</option>
                      {validLocationsForFormat(editData.format ?? artifact.format).map((l) => (
                        <option key={l} value={l}>
                          {l}
                        </option>
                      ))}
                    </select>
                    {(editCopyData[copy.copy_id]?.location ?? copy.location) === 'Lent' && (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={editCopyData[copy.copy_id]?.borrower_name ?? copy.borrower_name ?? ''}
                          onChange={(e) =>
                            setEditCopyData((d) => ({
                              ...d,
                              [copy.copy_id]: {
                                ...d[copy.copy_id],
                                borrower_name: e.target.value || null,
                              },
                            }))
                          }
                          placeholder="Borrower name"
                          className="flex-1 rounded-lg bg-surface-container px-2 py-1 font-body text-sm text-primary focus:outline-none"
                        />
                        <input
                          type="date"
                          value={editCopyData[copy.copy_id]?.lent_date ?? copy.lent_date ?? ''}
                          onChange={(e) =>
                            setEditCopyData((d) => ({
                              ...d,
                              [copy.copy_id]: {
                                ...d[copy.copy_id],
                                lent_date: e.target.value || null,
                              },
                            }))
                          }
                          className="rounded-lg bg-surface-container px-2 py-1 font-body text-sm text-primary focus:outline-none"
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <>
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
                  </>
                )}
              </div>
            ))}
            {artifact.copies.length === 0 && (
              <p className="py-4 text-center font-body text-sm text-on-surface-variant">
                No copies recorded yet.
              </p>
            )}
          </div>
        </section>

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


        {/* Danger Zone — only in edit mode */}
        {isEditing && <section>
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
              {/* Pirated toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-body text-sm font-semibold text-on-surface">
                    {artifact.is_pirated ? 'Pirated Copy' : 'Pirated Flag'}
                  </p>
                  <p className="font-body text-xs text-on-surface-variant">
                    {artifact.is_pirated
                      ? 'This artifact is flagged as a pirated copy.'
                      : 'Flag this artifact as a pirated copy.'}
                  </p>
                </div>
                <button
                  onClick={() => pirateMutation.mutate(!artifact.is_pirated)}
                  disabled={pirateMutation.isPending}
                  className={cn(
                    'rounded-full px-4 py-2 font-label text-xs font-bold disabled:opacity-50',
                    artifact.is_pirated
                      ? 'bg-error text-on-error'
                      : 'bg-surface-container-highest text-on-surface',
                  )}
                >
                  {artifact.is_pirated ? 'Remove Flag' : 'Flag as Pirated'}
                </button>
              </div>

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
        </section>}
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

// --- Cover upload drop zone ---

function CoverDropZone({
  artifactId,
  onUpload,
}: {
  artifactId: string;
  onUpload: () => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    if (!file.type.startsWith('image/')) return;
    setIsUploading(true);
    try {
      await uploadCover(artifactId, file);
      onUpload();
    } catch {
      // error handled silently
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div
      className={`absolute inset-0 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed transition-colors cursor-pointer ${
        isDragging
          ? 'border-primary bg-primary/20'
          : 'border-on-surface/30 bg-surface/60 hover:border-primary/50'
      }`}
      onClick={() => fileInputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      {isUploading ? (
        <span className="material-symbols-outlined text-primary animate-spin text-3xl">progress_activity</span>
      ) : (
        <>
          <span className="material-symbols-outlined text-on-surface/60 text-3xl">upload</span>
          <span className="mt-1 text-xs text-on-surface/60 font-label">Drop or click to upload cover</span>
        </>
      )}
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
    <div className="rounded-2xl bg-surface-container-low p-4">
      <span className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
        {label}
      </span>
      {typeof value === 'string' ? (
        <p className="mt-1 font-headline text-xl text-primary">{value}</p>
      ) : (
        <div className="mt-1">{value}</div>
      )}
    </div>
  );
}
