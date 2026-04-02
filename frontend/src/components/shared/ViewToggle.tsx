interface ViewToggleProps {
  view: 'grid' | 'list';
  onChange: (v: 'grid' | 'list') => void;
}

export default function ViewToggle({ view, onChange }: ViewToggleProps) {
  return (
    <div className="inline-flex items-center bg-surface-container-low rounded-xl overflow-hidden">
      <button
        onClick={() => onChange('list')}
        className={`p-2 transition-colors ${
          view === 'list'
            ? 'bg-primary text-on-primary'
            : 'text-secondary hover:text-primary'
        }`}
        aria-label="List view"
      >
        <span className="material-symbols-outlined text-[20px]">view_list</span>
      </button>
      <button
        onClick={() => onChange('grid')}
        className={`p-2 transition-colors ${
          view === 'grid'
            ? 'bg-primary text-on-primary'
            : 'text-secondary hover:text-primary'
        }`}
        aria-label="Grid view"
      >
        <span className="material-symbols-outlined text-[20px]">grid_view</span>
      </button>
    </div>
  );
}
