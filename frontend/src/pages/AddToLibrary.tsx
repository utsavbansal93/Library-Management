import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { createArtifact } from '../api/artifacts';
import { ARTIFACT_FORMATS, LOCATIONS, OWNERS } from '../types';
import type { ArtifactCreate } from '../types';

function CollapsibleSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-2xl bg-surface-container-lowest">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-5 py-4"
      >
        <span className="font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
          {title}
        </span>
        <span
          className={`material-symbols-outlined text-on-surface-variant text-lg transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        >
          expand_more
        </span>
      </button>
      <div
        className={`overflow-hidden transition-all duration-200 ${open ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}`}
      >
        <div className="flex flex-col gap-4 px-5 pb-5">{children}</div>
      </div>
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
      {children}
    </label>
  );
}

export default function AddToLibrary() {
  const navigate = useNavigate();
  const submitGuard = useRef(false);

  interface FormState {
    title: string;
    format: string;
    publisher: string | null;
    edition_year: number | null;
    size: string | null;
    location: string | null;
    condition: string | null;
    owner: string | undefined;
    isbn_or_upc: string | null;
    notes: string | null;
  }

  const [form, setForm] = useState<FormState>({
    title: '',
    format: '',
    publisher: null,
    edition_year: null,
    size: null,
    location: null,
    condition: null,
    owner: undefined,
    isbn_or_upc: null,
    notes: null,
  });

  const mutation = useMutation({
    mutationFn: (data: FormState) => {
      const { location: _loc, condition: _cond, ...artifactData } = data;
      return createArtifact(artifactData as ArtifactCreate);
    },
    onSuccess: (result) => {
      submitGuard.current = false;
      navigate(`/artifacts/${result.artifact_id}`);
    },
    onError: () => {
      submitGuard.current = false;
    },
  });

  const updateField = useCallback(
    <K extends keyof FormState>(key: K, value: FormState[K]) => {
      setForm((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitGuard.current) return;
    if (!form.title.trim() || !form.format) return;
    submitGuard.current = true;
    mutation.mutate(form);
  }

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">Add to Library</h1>
      </header>

      <form onSubmit={handleSubmit} className="mx-auto max-w-2xl">
        {/* Required fields */}
        <div className="mb-6 flex flex-col gap-4 rounded-2xl bg-surface-container-lowest p-5">
          <div>
            <FieldLabel>Title *</FieldLabel>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => updateField('title', e.target.value)}
              placeholder="Enter artifact title"
              className="mt-1 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <div>
            <FieldLabel>Format *</FieldLabel>
            <select
              required
              value={form.format}
              onChange={(e) => updateField('format', e.target.value)}
              className="mt-1 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">Select format</option>
              {ARTIFACT_FORMATS.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Collapsible sections */}
        <div className="flex flex-col gap-3">
          <CollapsibleSection title="Publisher & Year">
            <div>
              <FieldLabel>Publisher</FieldLabel>
              <input
                type="text"
                value={form.publisher ?? ''}
                onChange={(e) => updateField('publisher', e.target.value || null)}
                placeholder="e.g. DC Comics, Penguin"
                className="mt-1 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
            <div>
              <FieldLabel>Edition Year</FieldLabel>
              <input
                type="number"
                value={form.edition_year ?? ''}
                onChange={(e) =>
                  updateField('edition_year', e.target.value ? parseInt(e.target.value, 10) : null)
                }
                placeholder="e.g. 2023"
                className="mt-1 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Physical Details">
            <div>
              <FieldLabel>Size</FieldLabel>
              <select
                value={form.size ?? ''}
                onChange={(e) => updateField('size', e.target.value || null)}
                className="mt-1 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="">Select size</option>
                <option value="Large">Large</option>
                <option value="Small">Small</option>
              </select>
            </div>
            <div>
              <FieldLabel>Location</FieldLabel>
              <select
                value={form.location ?? ''}
                onChange={(e) => updateField('location', e.target.value || null)}
                className="mt-1 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="">Select location</option>
                {LOCATIONS.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <FieldLabel>Condition</FieldLabel>
              <input
                type="text"
                value={form.condition ?? ''}
                onChange={(e) => updateField('condition', e.target.value || null)}
                placeholder="e.g. Near Mint, Good"
                className="mt-1 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Ownership">
            <div>
              <FieldLabel>Owner</FieldLabel>
              <select
                value={form.owner ?? ''}
                onChange={(e) => updateField('owner', e.target.value || undefined)}
                className="mt-1 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="">Select owner</option>
                {OWNERS.map((o) => (
                  <option key={o} value={o}>
                    {o}
                  </option>
                ))}
              </select>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Identifiers">
            <div>
              <FieldLabel>ISBN or UPC</FieldLabel>
              <input
                type="text"
                value={form.isbn_or_upc ?? ''}
                onChange={(e) => updateField('isbn_or_upc', e.target.value || null)}
                placeholder="e.g. 978-0-13-468599-1"
                className="mt-1 w-full rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Notes">
            <div>
              <FieldLabel>Notes</FieldLabel>
              <textarea
                value={form.notes ?? ''}
                onChange={(e) => updateField('notes', e.target.value || null)}
                rows={4}
                placeholder="Any additional notes about this artifact..."
                className="mt-1 w-full resize-y rounded-xl bg-surface-container-low px-4 py-3 font-body text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </CollapsibleSection>
        </div>

        {/* Error message */}
        {mutation.isError && (
          <div className="mt-6 rounded-2xl bg-error-container p-4 text-on-error-container">
            <p className="font-body text-sm">
              Failed to create artifact.{' '}
              {mutation.error instanceof Error ? mutation.error.message : 'Unknown error.'}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="mt-8 flex items-center gap-4">
          <button
            type="submit"
            disabled={mutation.isPending || !form.title.trim() || !form.format}
            className="rounded-xl bg-primary px-6 py-3 font-body text-sm font-medium text-on-primary transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {mutation.isPending ? 'Saving...' : 'Commit to Library'}
          </button>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="rounded-xl px-6 py-3 font-body text-sm font-medium text-on-surface-variant hover:bg-surface-container-low"
          >
            Discard
          </button>
        </div>
      </form>
    </div>
  );
}
