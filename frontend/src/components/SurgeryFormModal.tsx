import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Dog, Centre, TokenPayload } from '../types';
import { useAuth } from '../contexts/AuthContext';

interface SurgeryFormModalProps {
  readonly onClose: () => void;
  readonly onSubmit: (data: { dog_id: string; centre_id: string; staff_id: string; surgery_type: string; weight?: number; complications?: string }) => Promise<void>;
}

export function SurgeryFormModal({ onClose, onSubmit }: SurgeryFormModalProps) {
  const { user } = useAuth();
  const [dogs, setDogs] = useState<Dog[]>([]);
  const [centres, setCentres] = useState<Centre[]>([]);
  const [formData, setFormData] = useState({
    dog_id: '',
    centre_id: '',
    surgery_type: 'spay',
    weight: '',
    complications: '',
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.getSurgeries().catch(() => undefined); // warm auth if needed
    api.getCentres({ limit: 100 })
      .then((res) => setCentres(Array.isArray(res) ? res : res.data))
      .catch(() => setError('Failed to load centres'));
    api.getDogs()
      .then(setDogs)
      .catch(() => setError('Failed to load registered dogs. Register a dog first.'));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.dog_id || !formData.centre_id || !formData.surgery_type) {
      setError('Dog, centre, and surgery type are required');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        dog_id: formData.dog_id,
        centre_id: formData.centre_id,
        staff_id: (user as TokenPayload | null)?.user_id ?? '',
        surgery_type: formData.surgery_type,
        weight: formData.weight ? Number.parseFloat(formData.weight) : undefined,
        complications: formData.complications || undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record surgery');
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose} onKeyDown={(e) => { if (e.key === 'Escape') onClose(); }}>
      <div
        className="bg-surface-container-high border border-outline-variant rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="surgery-modal-title"
      >
        <div className="flex justify-between items-center p-4 border-b border-outline-variant">
          <h2 id="surgery-modal-title" className="font-headline-sm text-headline-sm font-semibold text-on-surface">Record Surgery</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="text-on-surface-variant hover:text-on-surface">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="bg-error-container text-on-error-container px-3 py-2 rounded font-body-sm text-body-sm" role="alert">
              {error}
            </div>
          )}
          <div>
            <label htmlFor="surgery-dog" className="block font-label-md text-label-md text-on-surface-variant mb-1">Dog *</label>
            <select
              id="surgery-dog"
              value={formData.dog_id}
              onChange={(e) => {
                const dog = dogs.find((d) => d.id === e.target.value);
                setFormData((prev) => ({
                  ...prev,
                  dog_id: e.target.value,
                  centre_id: dog?.centre_id ?? prev.centre_id,
                }));
              }}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md focus:border-primary outline-none"
            >
              <option value="">Select a dog…</option>
              {dogs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.tag_id} ({d.sex === 'male' ? 'Male' : 'Female'}{d.age_estimate ? `, ~${d.age_estimate}y` : ''})
                </option>
              ))}
            </select>
            {dogs.length === 0 && !error && (
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">No dogs registered yet.</p>
            )}
          </div>
          <div>
            <label htmlFor="surgery-centre" className="block font-label-md text-label-md text-on-surface-variant mb-1">Centre *</label>
            <select
              id="surgery-centre"
              value={formData.centre_id}
              onChange={(e) => setFormData((prev) => ({ ...prev, centre_id: e.target.value }))}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md focus:border-primary outline-none"
            >
              <option value="">Select a centre…</option>
              {centres.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="surgery-type" className="block font-label-md text-label-md text-on-surface-variant mb-1">Surgery Type *</label>
            <select
              id="surgery-type"
              value={formData.surgery_type}
              onChange={(e) => setFormData((prev) => ({ ...prev, surgery_type: e.target.value }))}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md focus:border-primary outline-none"
            >
              <option value="spay">Spay</option>
              <option value="neuter">Neuter</option>
              <option value="vaccination">Vaccination</option>
              <option value="treatment">Treatment</option>
              <option value="emergency">Emergency</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="surgery-weight" className="block font-label-md text-label-md text-on-surface-variant mb-1">Weight (kg)</label>
              <input
                id="surgery-weight"
                type="number"
                step="0.1"
                min="0"
                value={formData.weight}
                onChange={(e) => setFormData((prev) => ({ ...prev, weight: e.target.value }))}
                className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md focus:border-primary outline-none"
              />
            </div>
            <div>
              <label htmlFor="surgery-complications" className="block font-label-md text-label-md text-on-surface-variant mb-1">Complications</label>
              <input
                id="surgery-complications"
                type="text"
                value={formData.complications}
                onChange={(e) => setFormData((prev) => ({ ...prev, complications: e.target.value }))}
                placeholder="None"
                className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md focus:border-primary outline-none"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-outline-variant rounded font-label-bold text-label-bold text-on-surface hover:bg-surface-container-highest transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="bg-primary text-on-primary font-label-bold text-label-bold px-4 py-2 rounded transition-colors hover:bg-primary-container disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Recording…' : 'Record Surgery'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
