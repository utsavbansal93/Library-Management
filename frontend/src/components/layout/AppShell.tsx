import { useState, useCallback } from 'react';
import { Outlet, useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import TopNav from './TopNav';
import Sidebar from './Sidebar';

export default function AppShell() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Consider active only if we are on the library index page
  const activeCategory = location.pathname === '/' 
    ? (searchParams.get('category') || 'all') 
    : '';

  const handleCategoryChange = useCallback(
    (category: string) => {
      const next = new URLSearchParams(searchParams);
      if (category === 'all') {
        next.delete('category');
      } else {
        next.set('category', category);
      }
      navigate({ pathname: '/', search: next.toString() });
    },
    [navigate, searchParams],
  );

  return (
    <div className="min-h-screen bg-surface">
      <TopNav onMenuToggle={() => setSidebarOpen((prev) => !prev)} />

      <div className="flex">
        <Sidebar
          activeCategory={activeCategory}
          onCategoryChange={handleCategoryChange}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        <main className="flex-1 min-w-0 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
