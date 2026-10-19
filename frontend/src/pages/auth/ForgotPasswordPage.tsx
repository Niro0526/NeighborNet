import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSent(true);
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold tracking-tight text-[#182B25]">Reset Password</h2>
        <p className="mt-1 text-xs text-[#64748B]">
          Enter your registered email address to receive password recovery instructions.
        </p>
      </div>

      {sent ? (
        <div className="rounded-2xl bg-emerald-50 p-5 border border-emerald-200 text-center space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-[#16866A]">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <h3 className="text-sm font-bold text-[#182B25]">Password Reset Link Sent</h3>
          <p className="text-xs text-[#64748B] leading-relaxed">
            (Simulated action) Recovery instructions sent to <span className="font-semibold text-[#182B25]">{email}</span>.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-[#16866A] hover:underline pt-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Sign In</span>
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="e.g. user@organization.lk"
              className="w-full rounded-xl border border-[#E5EAE7] bg-white px-3.5 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-xl bg-[#16866A] py-2.5 px-4 text-xs font-bold text-white shadow-xs hover:bg-[#09664F] transition-all cursor-pointer"
          >
            Send Reset Instructions
          </button>

          <div className="text-center pt-2">
            <Link
              to="/login"
              className="inline-flex items-center gap-1 text-xs font-semibold text-[#64748B] hover:text-[#182B25]"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Sign In</span>
            </Link>
          </div>
        </form>
      )}
    </div>
  );
};
