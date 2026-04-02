import { useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProfileContext, getStoredProfile, setStoredProfile, clearStoredProfile } from './hooks/useProfile'
import type { Profile } from './types'
import AppShell from './components/layout/AppShell'
import MyLibrary from './pages/MyLibrary'
import ArtifactDetail from './pages/ArtifactDetail'
import WorkDetail from './pages/WorkDetail'
import StoryArcTimeline from './pages/StoryArcTimeline'
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
import NotFound from './pages/NotFound'

function App() {
  const [profile, setProfileState] = useState<Profile | null>(getStoredProfile)

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
            <Route path="stories" element={<ComicsBrowse />} />
            <Route path="review" element={<ReviewQueue />} />
            <Route path="collections/:collectionId" element={<CollectionDetail />} />
            <Route path="creators/:creatorId" element={<CreatorDetail />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ProfileContext.Provider>
  )
}

export default App
