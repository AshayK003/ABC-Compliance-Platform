import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Centre } from '../types';

interface FundRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: FundRequestFormData) => Promise<void>;
}

interface FundRequestFormData {
  centreId: string;
  grantId: string;
  amount: number;
  purpose: string;
  financialYear: string;
}

interface FundRequestFormErrors {
  centreId?: string;
  grantId?: string;
  amount?: string;
  purpose?: string;
  financialYear?: string;
}

export function FundRequestModal({ isOpen, onClose, onSubmit }: FundRequestModalProps) {
  const [centres, setCentres] = useState<Centre[]>([]);
  const [grants, setGrants] = useState<Array<{ id: string; awbi_ref: string; amount: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<FundRequestFormErrors>({});

  const [formData, setFormData] = useState<FundRequestFormData>({
    centreId: '',
    grantId: '',
    amount: 0,
    purpose: '',
    financialYear: new Date().getFullYear().toString(),
  });

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [centreData, grantData] = await Promise.all([
        api.getCentres({ limit: 100 }),
        api.getGrants(),
      ]);
      
      const centresArray = Array.isArray(centreData) ? centreData : (centreData.data ?? []);
      const grantsArray = Array.isArray(grantData) ? grantData : [];
      
      setCentres(centresArray.filter(c => c.status === 'active'));
      setGrants(grantsArray.filter(g => g.status === 'active'));
    } catch (error) {
      console.error('Failed to load modal data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof FundRequestFormData, value: string | number) => {
    if (field === 'amount') {
      const numValue = typeof value === 'string' ? (parseFloat(value) || 0) : (value as number);
      setFormData(prev => ({ ...prev, amount: numValue }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
    if (errors[field as keyof FundRequestFormData]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FundRequestFormErrors = {};
    if (!formData.centreId) newErrors.centreId = 'Centre is required';
    if (!formData.grantId) newErrors.grantId = 'Grant is required';
    const amountValue = Number(formData.amount);
    if (!amountValue || amountValue <= 0) newErrors.amount = 'Valid amount is required';
    if (!formData.purpose.trim()) newErrors.purpose = 'Purpose is required';
    if (!formData.financialYear.trim()) newErrors.financialYear = 'Financial year is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      setSubmitting(true);
      await onSubmit(formData);
      onClose();
      setFormData({
        centreId: '',
        grantId: '',
        amount: 0,
        purpose: '',
        financialYear: new Date().getFullYear().toString(),
      });
    } catch (error) {
      console.error('Failed to submit fund request:', error);
      setErrors({ purpose: 'Failed to submit request' });
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-surface-container-high w-full max-w-md rounded-xl border border-outline-variant shadow-xl animate-in fade-in zoom-in-95 duration-200">
        <div className="p-6 border-b border-outline-variant flex justify-between items-center">
          <h2 className="font-headline-md text-headline-md font-bold text-on-surface">New Fund Request</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded text-on-surface-variant hover:bg-surface-container transition-colors"
            aria-label="Close modal"
          >
            <span className="material-symbols-outlined text-[24px]">close</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent"></div>
            </div>
          ) : (
            <>
              <div>
                <label htmlFor="centreId" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
                  Centre *
                </label>
                <select
                  id="centreId"
                  value={formData.centreId}
                  onChange={(e) => handleChange('centreId', e.target.value)}
                  className={`w-full bg-background border rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all ${errors.centreId ? 'border-error' : 'border-outline-variant'}`}
                  disabled={loading}
                  required
                >
                  <option value="" disabled>Select a centre</option>
                  {centres.map(c => (
                    <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
                  ))}
                </select>
                {errors.centreId && <p className="mt-1 text-body-sm text-error">{errors.centreId}</p>}
              </div>

              <div>
                <label htmlFor="grantId" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
                  Grant *
                </label>
                <select
                  id="grantId"
                  value={formData.grantId}
                  onChange={(e) => handleChange('grantId', e.target.value)}
                  className={`w-full bg-background border rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all ${errors.grantId ? 'border-error' : 'border-outline-variant'}`}
                  disabled={loading}
                  required
                >
                  <option value="" disabled>Select a grant</option>
                  {grants.map(g => (
                    <option key={g.id} value={g.id}>{g.awbi_ref} — ₹{(g.amount / 100000).toFixed(1)}L</option>
                  ))}
                </select>
                {errors.grantId && <p className="mt-1 text-body-sm text-error">{errors.grantId}</p>}
              </div>

              <div>
                <label htmlFor="financialYear" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
                  Financial Year *
                </label>
                <input
                  id="financialYear"
                  type="text"
                  value={formData.financialYear}
                  onChange={(e) => handleChange('financialYear', e.target.value)}
                  className={`w-full bg-background border rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all ${errors.financialYear ? 'border-error' : 'border-outline-variant'}`}
                  placeholder="e.g., 2024-25"
                  required
                />
                {errors.financialYear && <p className="mt-1 text-body-sm text-error">{errors.financialYear}</p>}
              </div>

              <div>
                <label htmlFor="amount" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
                  Amount (₹) *
                </label>
                <input
                  id="amount"
                  type="number"
                  value={formData.amount}
                  onChange={(e) => handleChange('amount', parseFloat(e.target.value) || 0)}
                  className={`w-full bg-background border rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all ${errors.amount ? 'border-error' : 'border-outline-variant'}`}
                  min="1"
                  step="1000"
                  placeholder="Enter amount in rupees"
                  required
                />
                {errors.amount && <p className="mt-1 text-body-sm text-error">{errors.amount}</p>}
              </div>

              <div>
                <label htmlFor="purpose" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
                  Purpose *
                </label>
                <textarea
                  id="purpose"
                  value={formData.purpose}
                  onChange={(e) => handleChange('purpose', e.target.value)}
                  rows={3}
                  className={`w-full bg-background border rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all resize-none ${errors.purpose ? 'border-error' : 'border-outline-variant'}`}
                  placeholder="Brief description of the fund request purpose"
                  required
                />
                {errors.purpose && <p className="mt-1 text-body-sm text-error">{errors.purpose}</p>}
              </div>
            </>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-outline-variant">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-on-surface-variant font-label-bold text-label-bold rounded hover:bg-surface-container transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || loading}
              className="px-4 py-2 bg-primary text-on-primary font-label-bold text-label-bold rounded hover:bg-primary-container transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-on-primary/30 border-t-on-primary"></div>
                  Submitting...
                </>
              ) : (
                'Submit Request'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}