import { useNavigate } from 'react-router-dom';

export default function BackButton({ fallback = '/' }: { fallback?: string }) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => {
        if (window.history.length > 1) {
          navigate(-1);
        } else {
          navigate(fallback);
        }
      }}
      className="mb-6 inline-flex items-center gap-1 font-body text-sm text-secondary transition-colors hover:text-primary"
    >
      <span className="material-symbols-outlined text-[18px]">arrow_back</span>
      Back
    </button>
  );
}
