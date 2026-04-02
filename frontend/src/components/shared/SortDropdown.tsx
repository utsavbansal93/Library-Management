interface SortOption {
  value: string;
  label: string;
}

interface SortDropdownProps {
  value: string;
  onChange: (v: string) => void;
  options: SortOption[];
}

export default function SortDropdown({ value, onChange, options }: SortDropdownProps) {
  return (
    <div className="relative inline-block">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none bg-surface-container-low text-on-surface font-body text-sm rounded-xl pl-4 pr-10 py-2 focus:outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px] pointer-events-none">
        expand_more
      </span>
    </div>
  );
}
