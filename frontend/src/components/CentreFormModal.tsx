import { useState, useEffect } from 'react';
import type { Centre } from '../types';

interface CentreFormModalProps {
  centre: Centre | null;
  onClose: () => void;
  onSubmit: (data: { name: string; code: string; district: string; state: string; capacity?: number }) => Promise<void>;
}

export function CentreFormModal({ centre, onClose, onSubmit }: CentreFormModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    district: '',
    state: '',
    capacity: '',
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (centre) {
      setFormData({
        name: centre.name,
        code: centre.code,
        district: centre.district,
        state: centre.state,
        capacity: String(centre.capacity || ''),
      });
    } else {
      setFormData({ name: '', code: '', district: '', state: '', capacity: '' });
    }
  }, [centre]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.name || !formData.code || !formData.district || !formData.state) {
      setError('All fields except capacity are required');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        name: formData.name,
        code: formData.code,
        district: formData.district,
        state: formData.state,
        capacity: formData.capacity ? Number.parseInt(formData.capacity, 10) : undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save centre');
    } finally {
      setSubmitting(false);
    }
  };

  const submitText = submitting ? 'Saving...' : (centre ? 'Update' : 'Create');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-surface-container-high border border-outline-variant rounded-lg w-full max-w-md overflow-hidden">
        <div className="p-4 border-b border-outline-variant flex justify-between items-center">
          <h2 className="font-headline-sm text-headline-sm text-on-surface">
            {centre ? 'Edit Centre' : 'Add New Centre'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 text-on-surface-variant hover:text-on-surface hover:bg-surface-container rounded-full transition-colors"
            disabled={submitting}
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="p-3 bg-error-container/20 border border-error/30 rounded text-error text-body-sm">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="name" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
              Centre Name *
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
              placeholder="Enter centre name"
              required
              disabled={submitting}
            />
          </div>

          <div>
            <label htmlFor="code" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
              Centre Code *
            </label>
            <input
              id="code"
              type="text"
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
              placeholder="e.g., MNAH-001"
              required
              disabled={submitting}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="district" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
                District *
              </label>
              <input
                id="district"
                type="text"
                value={formData.district}
                onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
                placeholder="Enter district"
                required
                disabled={submitting}
              />
            </div>

            <div>
              <label htmlFor="state" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
                State *
              </label>
              <input
                id="state"
                type="text"
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
                placeholder="Enter state"
                required
                disabled={submitting}
              />
            </div>
          </div>

          <div>
            <label htmlFor="capacity" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
              Capacity (Monthly)
            </label>
            <input
              id="capacity"
              type="number"
              value={formData.capacity}
              onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
              placeholder="Monthly surgery capacity"
              min="0"
              disabled={submitting}
            />
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="flex-1 bg-surface-container-high border border-outline-variant text-on-surface font-label-bold text-label-bold px-4 py-2.5 rounded transition-colors hover:bg-surface-variant"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-primary text-on-primary font-label-bold text-label-bold px-4 py-2.5 rounded transition-colors hover:bg-primary-container disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitText}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}