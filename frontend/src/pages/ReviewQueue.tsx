import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listFlags, updateFlag } from '../api/flags';
import type { FlagSummary } from '../types';

const FLAG_TYPE_STYLES: Record<string, string> = {
  missing_data: 'bg-tertiary-fixed text-on-tertiary-fixed',
  duplicate: 'bg-error text-on-error',
  bad_data: 'bg-secondary text-on-secondary',
  review_needed: 'bg-primary text-on-primary',
};

function flagTypeStyle(type: string): string {
  return FLAG_TYPE_STYLES[type] ?? 'bg-surface-container-highest text-on-surface-variant';
}

function entityLink(flag: FlagSummary): { to: string; label: string } {
  switch (flag.entity_type) {
    case 'artifact':
      return { to: `/artifacts/${flag.entity_id}`, label: `Artifact: ${flag.entity_id.slice(0, 8)}` };
    case 'work':
      return { to: `/works/${flag.entity_id}`, label: `Work: ${flag.entity_id.slice(0, 8)}` };
    case 'creator':
      return { to: `/creators/${flag.entity_id}`, label: `Creator: ${flag.entity_id.slice(0, 8)}` };
    case 'collection':
      return { to: `/collections/${flag.entity_id}`, label: `Collection: ${flag.entity_id.slice(0, 8)}` };
    case 'arc':
      return { to: `/arcs/${flag.entity_id}`, label: `Arc: ${flag.entity_id.slice(0, 8)}` };
    default:
      return { to: '#', label: `${flag.entity_type}: ${flag.entity_id.slice(0, 8)}` };
  }
}

function FlagRow({ flag }: { flag: FlagSummary }) {
  const queryClient = useQueryClient();
  const link = entityLink(flag);

  const resolveMutation = useMutation({
    mutationFn: () => updateFlag(flag.flag_id, { action: 'resolve' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['flags'] }),
  });

  const dismissMutation = useMutation({
    mutationFn: () => updateFlag(flag.flag_id, { action: 'dismiss' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['flags'] }),
  });

  const isPending = resolveMutation.isPending || dismissMutation.isPending;

  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-surface-container-lowest p-5 sm:flex-row sm:items-start sm:gap-4">
      <div className="min-w-0 flex-1">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span
            className={`inline-block rounded-full px-3 py-0.5 font-label text-[10px] font-bold uppercase tracking-widest ${flagTypeStyle(flag.flag_type)}`}
          >
            {flag.flag_type.replace(/_/g, ' ')}
          </span>
          <Link
            to={link.to}
            className="font-body text-sm font-medium text-primary hover:underline"
          >
            {link.label}
          </Link>
        </div>
        <p className="font-body text-sm text-on-surface">{flag.description}</p>
        {flag.suggested_fix && (
          <p className="mt-1 font-body text-xs text-on-surface-variant">
            Suggested fix: {flag.suggested_fix}
          </p>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <button
          onClick={() => resolveMutation.mutate()}
          disabled={isPending}
          className="rounded-xl bg-primary px-4 py-2 font-body text-xs font-medium text-on-primary transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          Resolve
        </button>
        <button
          onClick={() => dismissMutation.mutate()}
          disabled={isPending}
          className="rounded-xl px-4 py-2 font-body text-xs font-medium text-on-surface-variant hover:bg-surface-container-low disabled:opacity-50"
        >
          Dismiss
        </button>
        <Link
          to={link.to}
          className="rounded-xl px-4 py-2 font-body text-xs font-medium text-secondary hover:bg-surface-container-low"
        >
          Edit
        </Link>
      </div>
    </div>
  );
}

export default function ReviewQueue() {
  const {
    data: flags,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['flags', { status: 'open' }],
    queryFn: () => listFlags({ status: 'open' }),
  });

  const items = flags ?? [];

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">Review Queue</h1>
        <p className="mt-2 font-body text-base text-on-surface-variant">
          {isLoading
            ? 'Loading flags...'
            : `${items.length} open flag${items.length !== 1 ? 's' : ''}`}
        </p>
      </header>

      {isLoading && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-2xl bg-surface-container-low" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-2xl bg-error-container p-6 text-on-error-container">
          <p className="font-body text-sm">
            Failed to load flags. {error instanceof Error ? error.message : 'Unknown error.'}
          </p>
        </div>
      )}

      {!isLoading && !isError && items.length === 0 && (
        <div className="flex flex-col items-center gap-4 py-20">
          <span className="material-symbols-outlined text-5xl text-primary">
            check_circle
          </span>
          <p className="font-body text-base text-on-surface-variant">
            All clear! No flags to review.
          </p>
        </div>
      )}

      {!isLoading && !isError && items.length > 0 && (
        <div className="flex flex-col gap-3">
          {items.map((flag) => (
            <FlagRow key={flag.flag_id} flag={flag} />
          ))}
        </div>
      )}
    </div>
  );
}
