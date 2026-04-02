import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getArc } from '../api/arcs';
import CoverImage from '../components/shared/CoverImage';
import type { WorkInArc, ArcBrief } from '../types';

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

function WorkCard({ work, position }: { work: WorkInArc; position: number }) {
  const artifactId = work.work?.work_id;

  return (
    <div className="flex items-center gap-4 rounded-2xl bg-surface-container-lowest p-4">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-container-highest font-label text-xs font-bold text-on-surface-variant">
        {position}
      </span>
      <div className="h-18 w-12 shrink-0 overflow-hidden rounded-lg">
        {artifactId ? (
          <CoverImage artifactId={artifactId} title={work.work?.title ?? ''} size="sm" />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-surface-container-high">
            <span className="material-symbols-outlined text-on-surface-variant text-lg">
              auto_stories
            </span>
          </div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <Link
          to={`/works/${work.work?.work_id}`}
          className="font-body text-sm font-medium text-on-surface hover:underline"
        >
          {work.work?.title ?? 'Untitled'}
        </Link>
        {work.volume_run && (
          <p className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
            {work.volume_run.publisher}
          </p>
        )}
      </div>
    </div>
  );
}

function MissingCard({ position }: { position: number }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl bg-surface-container p-4 opacity-60">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-container-highest font-label text-xs font-bold text-on-surface-variant">
        {position}
      </span>
      <div className="flex h-18 w-12 shrink-0 items-center justify-center rounded-lg bg-surface-container-highest">
        <span className="material-symbols-outlined text-on-surface-variant text-lg">
          help_outline
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <span className="font-label text-[10px] font-bold uppercase tracking-widest text-error">
          Missing
        </span>
        <p className="font-body text-xs text-on-surface-variant">Position {position}</p>
      </div>
    </div>
  );
}

function SubArcSection({ subArc }: { subArc: ArcBrief }) {
  return (
    <Link
      to={`/arcs/${subArc.arc_id}`}
      className="flex items-center gap-3 rounded-2xl bg-surface-container-low p-4 transition-colors hover:bg-surface-container-high"
    >
      <span className="material-symbols-outlined text-lg text-secondary">subdirectory_arrow_right</span>
      <div className="min-w-0 flex-1">
        <h3 className="font-headline text-lg text-on-surface">{subArc.name}</h3>
        {subArc.total_parts != null && (
          <span className="font-body text-xs text-on-surface-variant">
            {subArc.total_parts} parts
          </span>
        )}
      </div>
      {subArc.completion_status && (
        <span className="rounded-full bg-surface-container-highest px-3 py-1 font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          {subArc.completion_status}
        </span>
      )}
      <span className="material-symbols-outlined text-on-surface-variant">chevron_right</span>
    </Link>
  );
}

export default function StoryArcTimeline() {
  const { arcId: arc_id } = useParams<{ arcId: string }>();
  const {
    data: arc,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['arc', arc_id],
    queryFn: () => getArc(arc_id!),
    enabled: !!arc_id,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface-container-low px-6 py-10 lg:px-12">
        <div className="mb-6 h-12 w-64 animate-pulse rounded-xl bg-surface-container" />
        <div className="mb-4 h-4 w-48 animate-pulse rounded bg-surface-container" />
        <div className="mb-8 h-2 w-full animate-pulse rounded-full bg-surface-container" />
        <div className="flex flex-col gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-2xl bg-surface-container" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-surface-container-low px-6 py-10 lg:px-12">
        <div className="rounded-2xl bg-error-container p-6 text-on-error-container">
          <p className="font-body text-sm">
            Failed to load story arc. {error instanceof Error ? error.message : 'Unknown error.'}
          </p>
        </div>
      </div>
    );
  }

  if (!arc) return null;

  const works = arc.works ?? [];
  const children = arc.children ?? [];
  const totalParts = arc.total_parts ?? works.length;
  const ownedCount = works.length;

  // Build position map for gap detection
  const positionMap = new Map<number, WorkInArc>();
  works.forEach((w) => {
    if (w.arc_position != null) {
      positionMap.set(w.arc_position, w);
    }
  });

  // Build the timeline items (including gaps)
  const timelineItems: { position: number; work: WorkInArc | null }[] = [];
  if (totalParts > 0) {
    for (let i = 1; i <= totalParts; i++) {
      const w = positionMap.get(i) ?? null;
      timelineItems.push({ position: i, work: w });
    }
    // Add any works with positions beyond total_parts
    works.forEach((w) => {
      if (w.arc_position != null && w.arc_position > totalParts) {
        timelineItems.push({ position: w.arc_position, work: w });
      }
    });
  } else {
    works
      .sort((a, b) => (a.arc_position ?? 0) - (b.arc_position ?? 0))
      .forEach((w) => {
        timelineItems.push({ position: w.arc_position ?? 0, work: w });
      });
  }

  return (
    <div className="min-h-screen bg-surface-container-low px-6 py-10 lg:px-12">
      {/* Hero */}
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">{arc.name}</h1>
        {arc.description && (
          <p className="mt-2 font-body text-base text-on-surface-variant">{arc.description}</p>
        )}
        <p className="mt-3 font-body text-lg text-on-surface">
          You have{' '}
          <span className="font-bold text-primary">{ownedCount}</span> of{' '}
          <span className="font-bold">{totalParts}</span> parts
        </p>
      </header>

      {/* Progress */}
      <div className="mb-10">
        <ProgressBar owned={ownedCount} total={totalParts} />
      </div>

      {/* Sub-arcs */}
      {children.length > 0 && (
        <section className="mb-10">
          <h2 className="mb-4 font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
            Sub-Arcs
          </h2>
          <div className="flex flex-col gap-3">
            {children.map((child) => (
              <SubArcSection key={child.arc_id} subArc={child} />
            ))}
          </div>
        </section>
      )}

      {/* Main works timeline */}
      <section>
        <h2 className="mb-4 font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
          Reading Order
        </h2>
        <div className="flex flex-col gap-2">
          {timelineItems.map((item) =>
            item.work ? (
              <WorkCard
                key={item.work.work?.work_id ?? item.position}
                work={item.work}
                position={item.position}
              />
            ) : (
              <MissingCard key={`missing-${item.position}`} position={item.position} />
            ),
          )}
          {timelineItems.length === 0 && (
            <p className="py-8 text-center font-body text-sm text-on-surface-variant">
              No works added to this arc yet.
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
