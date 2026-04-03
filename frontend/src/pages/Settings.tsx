import { useState, useEffect } from 'react';
import { useProfile } from '../hooks/useProfile';
import { LOCATIONS, PROFILES } from '../types';
import type { Profile } from '../types';

export default function Settings() {
  const { profile, setProfile } = useProfile();
  
  // Local storage state
  const [defaultLocation, setDefaultLocation] = useState(
    () => localStorage.getItem('alexandria-default-location') || ''
  );
  
  const [theme, setTheme] = useState(
    () => localStorage.getItem('alexandria-theme') || 'system'
  );

  const [saved, setSaved] = useState(false);

  // Sync to local storage
  useEffect(() => {
    localStorage.setItem('alexandria-default-location', defaultLocation);
  }, [defaultLocation]);

  useEffect(() => {
    localStorage.setItem('alexandria-theme', theme);
    // Dispatch storage event so App.tsx theme listener picks it up in same tab
    window.dispatchEvent(new StorageEvent('storage', { key: 'alexandria-theme', newValue: theme }));
  }, [theme]);

  // Flash saved indicator
  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <div className="mx-auto max-w-2xl">
        <header className="mb-10">
          <h1 className="font-headline text-5xl text-primary">Settings</h1>
          <p className="mt-2 font-body text-base text-on-surface-variant">
            Manage your personal preferences. These settings are saved only on this device.
          </p>
        </header>

        <div className="space-y-8">
          {/* Profile Settings */}
          <section className="rounded-2xl bg-surface-container-low p-6">
            <h2 className="mb-4 font-headline text-2xl text-primary">Profile</h2>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block font-label text-xs font-bold uppercase tracking-widest text-secondary">
                  Active Profile
                </label>
                <select
                  value={profile ?? ''}
                  onChange={(e) => {
                    setProfile(e.target.value as Profile);
                    handleSave();
                  }}
                  className="w-full rounded-xl bg-surface px-4 py-3 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  <option value="" disabled>Select a profile...</option>
                  {PROFILES.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
                <p className="mt-2 font-body text-xs text-on-surface-variant">
                  This profile is used across the application to track reading history and personal progress.
                </p>
              </div>
            </div>
          </section>

          {/* Library Defaults */}
          <section className="rounded-2xl bg-surface-container-low p-6">
            <h2 className="mb-4 font-headline text-2xl text-primary">Library Defaults</h2>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block font-label text-xs font-bold uppercase tracking-widest text-secondary">
                  Default Location
                </label>
                <select
                  value={defaultLocation}
                  onChange={(e) => {
                    setDefaultLocation(e.target.value);
                    handleSave();
                  }}
                  className="w-full rounded-xl bg-surface px-4 py-3 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  <option value="">No Default</option>
                  {LOCATIONS.map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
                <p className="mt-2 font-body text-xs text-on-surface-variant">
                  When adding new artifacts to the library, this location will be automatically applied to the first copy.
                </p>
              </div>
            </div>
          </section>

          {/* Appearance Settings */}
          <section className="rounded-2xl bg-surface-container-low p-6">
            <h2 className="mb-4 font-headline text-2xl text-primary">Appearance</h2>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block font-label text-xs font-bold uppercase tracking-widest text-secondary">
                  Theme Mode
                </label>
                <select
                  value={theme}
                  onChange={(e) => {
                    setTheme(e.target.value);
                    handleSave();
                  }}
                  className="w-full rounded-xl bg-surface px-4 py-3 font-body text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  <option value="system">System Default</option>
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                </select>
                <p className="mt-2 font-body text-xs text-on-surface-variant">
                  Select your preferred color scheme. System default follows your device settings.
                </p>
              </div>
            </div>
          </section>

          {/* Status Indicator */}
          <div className="flex justify-end">
            <span
              className={`font-label text-sm font-bold tracking-widest text-primary transition-opacity duration-300 ${
                saved ? 'opacity-100' : 'opacity-0'
              }`}
            >
              PREFERENCES SAVED
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
