import { useState, useCallback } from 'react';
import { Outlet, useSearchParams } from 'react-router-dom';
import TopNav from './TopNav';
import Sidebar from './Sidebar';

export default function AppShell() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const activeCategory = searchParams.get('category') || 'all';

  const handleCategoryChange = useCallback(
    (category: string) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (category === 'all') {
          next.delete('category');
        } else {
          next.set('category', category);
        }
        return next;
      });
    },
    [setSearchParams],
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
