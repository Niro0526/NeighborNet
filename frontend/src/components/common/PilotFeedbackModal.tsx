import React, { useState } from 'react';
import {
  MessageCircle,
  Star,
  Send,
  X,
  CheckCircle2,
} from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { PilotFeedbackCategory } from '../../types';

const CATEGORIES: { value: PilotFeedbackCategory; label: string; description: string }[] = [
  { value: 'PLATFORM_USABILITY', label: 'Platform Usability', description: 'Navigation, design, and overall ease of use' },
  { value: 'MATCHING_QUALITY', label: 'Matching Quality', description: 'CP-SAT allocation accuracy and efficiency' },
  { value: 'DELIVERY_COORDINATION', label: 'Delivery Coordination', description: 'Courier dispatch, timeline accuracy, and tracking' },
  { value: 'DISASTER_RESPONSE', label: 'Disaster Response', description: 'Emergency mode activation, relief coordination' },
  { value: 'SYSTEM_STABILITY', label: 'System Stability', description: 'Uptime, performance, and error handling' },
  { value: 'GENERAL_PILOT', label: 'General Pilot Feedback', description: 'Overall impressions and improvement suggestions' },
];

interface PilotFeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PilotFeedbackModal: React.FC<PilotFeedbackModalProps> = ({ isOpen, onClose }) => {
  const [category, setCategory] = useState<PilotFeedbackCategory>('GENERAL_PILOT');
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comments, setComments] = useState('');
  const [consent, setConsent] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (rating === 0) {
      setError('Please select a rating (1-5 stars).');
      return;
    }
    if (!comments.trim()) {
      setError('Please provide feedback comments.');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      await analyticsService.submitPilotFeedback({
        category,
        rating,
        comments: comments.trim(),
        consent_to_share_internally: consent,
      });
      setIsSubmitted(true);
    } catch (err: any) {
      setError(err.message || 'Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setCategory('GENERAL_PILOT');
    setRating(0);
    setComments('');
    setConsent(false);
    setIsSubmitted(false);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-3xl bg-white shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#E5EAE7] px-6 py-4 bg-gradient-to-r from-emerald-50 to-teal-50">
          <div className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-[#16866A]" />
            <h3 className="text-base font-extrabold text-[#182B25]">Pilot Feedback</h3>
          </div>
          <button
            onClick={handleClose}
            className="rounded-lg p-1.5 hover:bg-white/80 text-[#64748B] cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {isSubmitted ? (
            /* Success State */
            <div className="text-center py-6 space-y-3">
              <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500" />
              <h4 className="text-lg font-extrabold text-[#182B25]">Thank You!</h4>
              <p className="text-xs text-[#64748B] max-w-sm mx-auto">
                Your feedback has been recorded and will be reviewed by the Coordinator team
                to improve the NeighborNet AI pilot.
              </p>
              <button
                onClick={handleClose}
                className="rounded-xl bg-[#16866A] px-5 py-2 text-xs font-bold text-white hover:bg-[#09664F] cursor-pointer mt-2"
              >
                Close
              </button>
            </div>
          ) : (
            <>
              <p className="text-xs text-[#64748B]">
                Help us improve the NeighborNet AI platform during the pilot phase. Your responses
                are confidential and directly inform product improvements.
              </p>

              {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800">
                  {error}
                </div>
              )}

              {/* Category Selection */}
              <div>
                <label className="block text-xs font-bold text-[#182B25] mb-2">
                  Feedback Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value as PilotFeedbackCategory)}
                  className="w-full rounded-xl border border-[#E5EAE7] p-2.5 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none focus:ring-1 focus:ring-[#16866A] cursor-pointer"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label} — {c.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Star Rating */}
              <div>
                <label className="block text-xs font-bold text-[#182B25] mb-2">
                  Rating (1-5 Stars)
                </label>
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <button
                      key={s}
                      onClick={() => setRating(s)}
                      onMouseEnter={() => setHoverRating(s)}
                      onMouseLeave={() => setHoverRating(0)}
                      className="cursor-pointer p-0.5"
                    >
                      <Star
                        className={`h-7 w-7 transition-colors ${
                          s <= (hoverRating || rating)
                            ? 'fill-amber-400 text-amber-400'
                            : 'text-slate-300'
                        }`}
                      />
                    </button>
                  ))}
                  {rating > 0 && (
                    <span className="ml-2 text-xs font-bold text-[#182B25]">
                      {rating}/5
                    </span>
                  )}
                </div>
              </div>

              {/* Comments */}
              <div>
                <label className="block text-xs font-bold text-[#182B25] mb-2">
                  Comments & Suggestions
                </label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="What worked well? What needs improvement? Share specific scenarios or suggestions..."
                  rows={4}
                  className="w-full rounded-xl border border-[#E5EAE7] p-3 text-xs text-[#182B25] placeholder-[#94A3B8] focus:border-[#16866A] focus:outline-none focus:ring-1 focus:ring-[#16866A]"
                />
              </div>

              {/* Consent */}
              <div className="flex items-start gap-2">
                <input
                  type="checkbox"
                  id="consent-share"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  className="mt-0.5 rounded cursor-pointer accent-[#16866A]"
                />
                <label htmlFor="consent-share" className="text-[11px] text-[#64748B] cursor-pointer">
                  I consent to sharing this feedback internally with the NeighborNet AI pilot team
                  for product improvement purposes.
                </label>
              </div>

              {/* Submit */}
              <div className="flex items-center justify-end gap-3 pt-2 border-t border-[#E5EAE7]">
                <button
                  onClick={handleClose}
                  className="rounded-xl border border-[#E5EAE7] px-4 py-2 text-xs font-semibold text-[#64748B] hover:bg-[#F8FAF9] cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="flex items-center gap-1.5 rounded-xl bg-[#16866A] px-5 py-2 text-xs font-bold text-white hover:bg-[#09664F] cursor-pointer disabled:opacity-50"
                >
                  <Send className="h-3.5 w-3.5" />
                  <span>{isSubmitting ? 'Submitting...' : 'Submit Feedback'}</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PilotFeedbackModal;
