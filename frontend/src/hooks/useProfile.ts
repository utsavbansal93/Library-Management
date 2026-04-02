import { createContext, useContext } from 'react';
import type { Profile } from '../types';

const STORAGE_KEY = 'alexandria-profile';

export function getStoredProfile(): Profile | null {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'Utsav' || stored === 'Utkarsh' || stored === 'Som') return stored;
  return null;
}

export function setStoredProfile(profile: Profile) {
  localStorage.setItem(STORAGE_KEY, profile);
}

export function clearStoredProfile() {
  localStorage.removeItem(STORAGE_KEY);
}

interface ProfileContextValue {
  profile: Profile | null;
  setProfile: (p: Profile) => void;
  clearProfile: () => void;
}

export const ProfileContext = createContext<ProfileContextValue>({
  profile: null,
  setProfile: () => {},
  clearProfile: () => {},
});

export function useProfile() {
  return useContext(ProfileContext);
}
