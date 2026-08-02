import { useEffect } from 'react';
import { Link } from 'react-router-dom';

export function NotFound() {
  useEffect(() => {
    document.title = 'Page Not Found - ABC Compliance Platform';
  }, []);

  return (
    <div className="flex h-screen items-center justify-center bg-background p-4">
      <div className="text-center max-w-md">
        <div className="text-9xl font-bold text-primary/10 mb-4">404</div>
        <h1 className="text-headline-lg font-headline-lg font-bold text-on-surface mb-4">
          Page Not Found
        </h1>
        <p className="text-body-md text-body-md text-on-surface-variant mb-8">
          Sorry, we couldn&apos;t find the page you&apos;re looking for. It might have been moved or doesn&apos;t exist.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary text-on-primary font-label-bold text-label-bold rounded-lg hover:bg-primary-container transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">home</span>
            Go Home
          </Link>
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-outline-variant rounded-lg font-label-bold text-label-bold text-on-surface hover:bg-surface-container-high transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
}