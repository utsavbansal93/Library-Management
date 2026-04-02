import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getCreator } from '../api/creators';
import { formatRoleLabel } from '../lib/utils';
import type { CreatorRoleBrief } from '../types';

interface GroupedRole {
  role: string;
  label: string;
  entries: CreatorRoleBrief[];
}

function groupByRole(roles: CreatorRoleBrief[]): GroupedRole[] {
  const map = new Map<string, CreatorRoleBrief[]>();
  roles.forEach((r) => {
    const existing = map.get(r.role) ?? [];
    existing.push(r);
    map.set(r.role, existing);
  });

  return Array.from(map.entries()).map(([role, entries]) => ({
    role,
    label: formatRoleLabel(role),
    entries,
  }));
}

export default function CreatorDetail() {
  const { creatorId: creator_id } = useParams<{ creatorId: string }>();
  const {
    data: creator,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['creator', creator_id],
    queryFn: () => getCreator(creator_id!),
    enabled: !!creator_id,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
        <div className="mb-6 h-12 w-64 animate-pulse rounded-xl bg-surface-container-low" />
        <div className="mb-4 h-4 w-48 animate-pulse rounded bg-surface-container-low" />
        <div className="flex flex-col gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
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
            Failed to load creator. {error instanceof Error ? error.message : 'Unknown error.'}
          </p>
        </div>
      </div>
    );
  }

  if (!creator) return null;

  const groups = groupByRole(creator.roles ?? []);

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      {/* Hero */}
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">{creator.display_name}</h1>
        {creator.aliases && creator.aliases.length > 0 && (
          <p className="mt-2 font-body text-sm text-on-surface-variant">
            Also known as: {creator.aliases.join(', ')}
          </p>
        )}
      </header>

      {/* Works grouped by role */}
      {groups.length > 0 ? (
        <div className="flex flex-col gap-10">
          {groups.map((group) => (
            <section key={group.role}>
              <h2 className="mb-4 font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
                {group.label}
              </h2>
              <div className="overflow-hidden rounded-2xl bg-surface-container-lowest">
                {group.entries.map((entry, idx) => (
                  <div
                    key={entry.id}
                    className={`flex items-center gap-4 px-5 py-3 ${idx > 0 ? '' : ''}`}
                  >
                    <Link
                      to={`/works/${entry.creator_id}`}
                      className="min-w-0 flex-1 font-body text-sm font-medium text-on-surface hover:underline"
                    >
                      {entry.notes ?? entry.role}
                    </Link>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20">
          <span className="material-symbols-outlined text-5xl text-on-surface-variant">
            person
          </span>
          <p className="font-body text-sm text-on-surface-variant">
            No works linked to this creator yet.
          </p>
        </div>
      )}
    </div>
  );
}
