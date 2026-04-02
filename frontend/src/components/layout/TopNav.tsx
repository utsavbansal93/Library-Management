import { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useProfile } from '../../hooks/useProfile';
import { PROFILES } from '../../types';
import type { Profile } from '../../types';

const NAV_LINKS = [
  { label: 'My Library', to: '/' },
  { label: 'Stories & Series', to: '/stories' },
  { label: 'Review Queue', to: '/review' },
];

interface TopNavProps {
  onMenuToggle?: () => void;
}

export default function TopNav({ onMenuToggle }: TopNavProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile, setProfile } = useProfile();

  const [searchQuery, setSearchQuery] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  // Close profile dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function handleSearch(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  }

  const initial = profile ? profile.charAt(0).toUpperCase() : '?';

  return (
    <header className="sticky top-0 z-50 bg-[#fbf9f4]/80 glass-nav">
      <div className="flex items-center justify-between px-6 h-14">
        {/* Left section */}
        <div className="flex items-center gap-8">
          {/* Mobile hamburger */}
          <button
            onClick={onMenuToggle}
            className="md:hidden flex items-center justify-center text-primary"
            aria-label="Open menu"
          >
            <span className="material-symbols-outlined">menu</span>
          </button>

          <Link
            to="/"
            className="font-headline italic text-lg text-primary font-semibold tracking-wide whitespace-nowrap"
          >
            ALEXANDRIA CORE
          </Link>

          {/* Desktop nav links */}
          <nav className="hidden md:flex items-center gap-6">
            {NAV_LINKS.map((link) => {
              const isActive =
                link.to === '/'
                  ? location.pathname === '/'
                  : location.pathname.startsWith(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`font-body text-sm transition-colors pb-1 ${
                    isActive
                      ? 'text-primary border-b-2 border-primary font-semibold'
                      : 'text-secondary hover:text-primary'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right section */}
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative hidden sm:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[18px]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearch}
              placeholder="Search the archives..."
              className="bg-surface-container-low rounded-xl pl-10 pr-4 py-2 text-sm font-headline italic text-on-surface placeholder:text-outline-variant focus:outline-none focus:ring-2 focus:ring-primary/20 w-56 transition-all focus:w-72"
            />
          </div>

          {/* Profile avatar */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setProfileOpen((prev) => !prev)}
              className="w-8 h-8 rounded-full bg-primary text-on-primary flex items-center justify-center font-body text-sm font-bold"
              aria-label="Switch profile"
            >
              {initial}
            </button>

            {profileOpen && (
              <div className="absolute right-0 top-full mt-2 w-44 bg-surface-container-lowest rounded-xl shadow-[0_10px_30px_rgba(27,28,25,0.12)] overflow-hidden">
                <div className="px-4 py-2">
                  <span className="font-label text-[10px] uppercase tracking-widest text-on-surface-variant font-bold">
                    Switch Profile
                  </span>
                </div>
                {PROFILES.map((p) => (
                  <button
                    key={p}
                    onClick={() => {
                      setProfile(p as Profile);
                      setProfileOpen(false);
                    }}
                    className={`w-full text-left px-4 py-2.5 font-body text-sm transition-colors ${
                      profile === p
                        ? 'bg-surface-container-high font-semibold text-primary'
                        : 'text-on-surface hover:bg-surface-container-low'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Settings icon */}
          <button
            className="text-secondary hover:text-primary transition-colors"
            aria-label="Settings"
          >
            <span className="material-symbols-outlined text-[22px]">settings</span>
          </button>
        </div>
      </div>

      {/* Subtle divider */}
      <div className="bg-[#f2efe4] h-[1px]" />
    </header>
  );
}
