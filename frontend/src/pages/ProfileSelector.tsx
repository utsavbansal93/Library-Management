import { useNavigate } from 'react-router-dom';
import { useProfile } from '../hooks/useProfile';
import { PROFILES } from '../types';
import type { Profile } from '../types';

const PROFILE_COLORS: Record<Profile, string> = {
  Utsav: 'bg-primary',
  Utkarsh: 'bg-secondary',
  Som: 'bg-error',
};

const PROFILE_TEXT_COLORS: Record<Profile, string> = {
  Utsav: 'text-on-primary',
  Utkarsh: 'text-on-secondary',
  Som: 'text-on-error',
};

export default function ProfileSelector() {
  const { setProfile } = useProfile();
  const navigate = useNavigate();

  function handleSelect(profile: Profile) {
    setProfile(profile);
    navigate('/');
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface px-6">
      <h1 className="mb-12 font-headline text-5xl text-primary">Who&rsquo;s Reading?</h1>

      <div className="flex gap-8">
        {PROFILES.map((profile) => (
          <button
            key={profile}
            onClick={() => handleSelect(profile)}
            className="group flex flex-col items-center gap-4"
          >
            <div
              className={`flex h-28 w-28 items-center justify-center rounded-full ${PROFILE_COLORS[profile]} transition-shadow group-hover:shadow-lg group-hover:shadow-primary/20`}
            >
              <span
                className={`font-headline text-4xl ${PROFILE_TEXT_COLORS[profile]}`}
              >
                {profile[0]}
              </span>
            </div>
            <span className="font-body text-base font-medium text-on-surface group-hover:text-primary">
              {profile}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
