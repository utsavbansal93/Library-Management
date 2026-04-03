import { useEffect } from 'react';

interface DeleteConfirmDialogProps {
  title: string;
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function DeleteConfirmDialog({
  title,
  isOpen,
  onConfirm,
  onCancel,
}: DeleteConfirmDialogProps) {
  // Lock body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onCancel();
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Card */}
      <div className="relative bg-surface-container-lowest/80 backdrop-blur-xl rounded-xl shadow-[0_20px_60px_rgba(27,28,25,0.25)] p-6 max-w-sm w-full mx-4">
        <h3 className="font-headline text-lg text-on-surface mb-3">
          Delete Item
        </h3>
        <p className="font-body text-sm text-on-surface-variant leading-relaxed mb-6">
          Are you sure you want to delete <strong className="text-on-surface">{title}</strong>?
          This will remove it from your library.
        </p>

        <div className="flex items-center justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 font-body text-sm text-secondary hover:text-primary transition-colors rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-error text-on-error font-body text-sm font-semibold rounded-xl transition-colors hover:bg-error/90"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
