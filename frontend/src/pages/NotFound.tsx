import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface px-6">
      <span className="material-symbols-outlined mb-6 text-7xl text-on-surface-variant">
        explore_off
      </span>
      <h1 className="mb-2 font-headline text-4xl text-primary">Page not found</h1>
      <p className="mb-8 font-body text-base text-on-surface-variant">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link
        to="/"
        className="rounded-xl bg-primary px-6 py-3 font-body text-sm font-medium text-on-primary transition-opacity hover:opacity-90"
      >
        Back to Home
      </Link>
    </div>
  );
}
