import { useState, useCallback, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProfileContext, getStoredProfile, setStoredProfile, clearStoredProfile } from './hooks/useProfile'
import { ToastProvider } from './hooks/useToast'
import type { Profile } from './types'
import AppShell from './components/layout/AppShell'
import MyLibrary from './pages/MyLibrary'
import ArtifactDetail from './pages/ArtifactDetail'
import WorkDetail from './pages/WorkDetail'
import StoryArcTimeline from './pages/StoryArcTimeline'
import StoriesBrowse from './pages/StoriesBrowse'
import ComicsBrowse from './pages/ComicsBrowse'
import NovelsBrowse from './pages/NovelsBrowse'
import NonFictionBrowse from './pages/NonFictionBrowse'
import MagazinesBrowse from './pages/MagazinesBrowse'
import AddToLibrary from './pages/AddToLibrary'
import SearchResults from './pages/SearchResults'
import ProfileSelector from './pages/ProfileSelector'
import ReviewQueue from './pages/ReviewQueue'
import CollectionDetail from './pages/CollectionDetail'
import CreatorDetail from './pages/CreatorDetail'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'

function applyTheme() {
  const theme = localStorage.getItem('alexandria-theme') ?? 'system';
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = theme === 'dark' || (theme === 'system' && prefersDark);
  document.documentElement.classList.toggle('dark', isDark);
}

function App() {
  const [profile, setProfileState] = useState<Profile | null>(getStoredProfile)

  // Apply theme on mount and listen for changes
  useEffect(() => {
    applyTheme();
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'alexandria-theme') applyTheme();
    };
    window.addEventListener('storage', handleStorage);
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    mql.addEventListener('change', applyTheme);
    return () => {
      window.removeEventListener('storage', handleStorage);
      mql.removeEventListener('change', applyTheme);
    };
  }, [])

  const setProfile = useCallback((p: Profile) => {
    setStoredProfile(p)
    setProfileState(p)
  }, [])

  const handleClearProfile = useCallback(() => {
    clearStoredProfile()
    setProfileState(null)
  }, [])

  return (
    <ProfileContext.Provider value={{ profile, setProfile, clearProfile: handleClearProfile }}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* Profile selector — shown when no profile stored */}
            <Route
              path="/profile"
              element={<ProfileSelector />}
            />

            {/* All app routes wrapped in AppShell */}
            <Route element={
              profile ? <AppShell /> : <Navigate to="/profile" replace />
            }>
              <Route index element={<MyLibrary />} />
              <Route path="artifacts/:artifactId" element={<ArtifactDetail />} />
              <Route path="works/:workId" element={<WorkDetail />} />
              <Route path="arcs/:arcId" element={<StoryArcTimeline />} />
              <Route path="comics" element={<ComicsBrowse />} />
              <Route path="novels" element={<NovelsBrowse />} />
              <Route path="nonfiction" element={<NonFictionBrowse />} />
              <Route path="magazines" element={<MagazinesBrowse />} />
              <Route path="add" element={<AddToLibrary />} />
              <Route path="search" element={<SearchResults />} />
              <Route path="stories" element={<StoriesBrowse />} />
              <Route path="review" element={<ReviewQueue />} />
              <Route path="settings" element={<Settings />} />
              <Route path="collections/:collectionId" element={<CollectionDetail />} />
              <Route path="creators/:creatorId" element={<CreatorDetail />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </ProfileContext.Provider>
  )
}

export default App
