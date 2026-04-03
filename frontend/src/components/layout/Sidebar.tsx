import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface SidebarProps {
  activeCategory: string;
  onCategoryChange: (category: string) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

const CATEGORIES = [
  { key: 'all', label: 'ALL', icon: 'auto_stories' },
  { key: 'comics', label: 'COMICS & GRAPHIC NOVELS', icon: 'menu_book' },
  { key: 'novels', label: 'NOVELS', icon: 'book_2' },
  { key: 'nonfiction', label: 'NON-FICTION', icon: 'history_edu' },
  { key: 'magazines', label: 'MAGAZINES', icon: 'newspaper' },
];

function SidebarContent({
  activeCategory,
  onCategoryChange,
}: Pick<SidebarProps, 'activeCategory' | 'onCategoryChange'>) {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 pt-6 pb-4">
        <h2 className="font-headline text-xl text-primary font-semibold">
          The Archives
        </h2>
        <span className="font-label text-[10px] uppercase tracking-widest text-on-surface-variant font-bold">
          Personal Collection
        </span>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 space-y-1">
        {CATEGORIES.map((cat) => {
          const isActive = activeCategory === cat.key;
          return (
            <button
              key={cat.key}
              onClick={() => onCategoryChange(cat.key)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-all duration-200 rounded-r-full ${
                isActive
                  ? 'bg-surface font-bold shadow-sm text-primary'
                  : 'text-secondary hover:bg-[#ebe8d9] hover:translate-x-1'
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">
                {cat.icon}
              </span>
              <span className="font-label text-[11px] uppercase tracking-widest">
                {cat.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Add button */}
      <div className="px-4 pb-6">
        <button onClick={() => navigate('/add')} className="w-full flex items-center justify-center gap-2 bg-primary text-on-primary rounded-xl py-3 font-body text-sm font-semibold transition-colors hover:bg-primary-container">
          <span className="material-symbols-outlined text-[18px]">add</span>
          Add to Library
        </button>
      </div>
    </div>
  );
}

export default function Sidebar({
  activeCategory,
  onCategoryChange,
  isOpen = false,
  onClose,
}: SidebarProps) {
  // Lock body scroll when mobile overlay is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [isOpen]);

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:block sticky top-14 h-[calc(100vh-3.5rem)] w-72 bg-[#f2efe4] shrink-0 overflow-y-auto scrollbar-hide">
        <SidebarContent
          activeCategory={activeCategory}
          onCategoryChange={onCategoryChange}
        />
      </aside>

      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={onClose}
          />
          {/* Slide-in panel */}
          <aside className="absolute left-0 top-0 h-full w-72 bg-[#f2efe4] shadow-[4px_0_20px_rgba(27,28,25,0.12)] animate-slide-in">
            <div className="flex items-center justify-end px-4 pt-3">
              <button
                onClick={onClose}
                className="text-secondary hover:text-primary"
                aria-label="Close sidebar"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <SidebarContent
              activeCategory={activeCategory}
              onCategoryChange={(cat) => {
                onCategoryChange(cat);
                onClose?.();
              }}
            />
          </aside>
        </div>
      )}
    </>
  );
}
