import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../hooks';
import { ShieldCheck, ArrowRight, Code, Check } from 'lucide-react';
import { isApiMode } from '../../services/apiClient';

export const LoginPage: React.FC = () => {
  const { allUsers, login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState(isApiMode() ? '' : 'ravi.mendis@greenbites.lk');
  const [password, setPassword] = useState(isApiMode() ? '' : 'password123');
  const [showDevHelper, setShowDevHelper] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    try {
      const user = await login({ email, password });

      // Coordinator-only users redirect to administration workspace
      if (user.assignedRoles.length === 1 && user.assignedRoles[0] === 'COORDINATOR') {
        navigate('/admin/dashboard');
      } else {
        // Regular users and multi-role users redirect to unified smart dashboard
        navigate('/dashboard');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Login failed. Please verify credentials.');
    }
  };

  const autofillAccount = (targetEmail: string) => {
    setEmail(targetEmail);
    setPassword('password123');
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold tracking-tight text-[#182B25]">Sign In</h2>
        <p className="mt-1 text-xs text-[#64748B]">
          Enter your registered email address to access your NeighborNet AI account.
        </p>
      </div>

      {errorMsg && (
        <div className="mb-4 rounded-xl bg-red-50 p-3 border border-red-200 text-xs text-red-700">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-[#182B25] mb-1">Email Address</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="e.g. user@organization.lk"
            className="w-full rounded-xl border border-[#E5EAE7] bg-white px-3.5 py-2 text-xs text-[#182B25] placeholder-[#94A3B8] focus:border-[#16866A] focus:outline-none focus:ring-1 focus:ring-[#16866A]"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-bold text-[#182B25]">Password</label>
            <Link to="/forgot-password" className="text-[11px] font-semibold text-[#16866A] hover:underline">
              Forgot password?
            </Link>
          </div>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="••••••••••••"
            className="w-full rounded-xl border border-[#E5EAE7] bg-white px-3.5 py-2 text-xs text-[#182B25] placeholder-[#94A3B8] focus:border-[#16866A] focus:outline-none focus:ring-1 focus:ring-[#16866A]"
          />
        </div>

        <button
          type="submit"
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-[#16866A] py-2.5 px-4 text-xs font-bold text-white shadow-xs hover:bg-[#09664F] transition-all cursor-pointer"
        >
          <span>Sign In</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </form>

      <div className="mt-4 flex items-center justify-center gap-2 text-xs text-[#64748B]">
        <span>Don't have an account?</span>
        <Link to="/register" className="font-bold text-[#16866A] hover:underline">
          Register Organization
        </Link>
      </div>

      <div className="mt-6 rounded-xl bg-amber-50/70 p-3 border border-amber-200">
        <div className="flex items-center gap-2 text-amber-800 text-[11px] font-bold">
          <ShieldCheck className="h-3.5 w-3.5 text-amber-700" />
          <span>Automatic Permission Detection</span>
        </div>
        <p className="mt-0.5 text-[10px] text-amber-700 leading-normal">
          One unified portal for all participants. Your approved role features (surplus food, community requests, or deliveries) will be dynamically loaded upon authentication.
        </p>
      </div>

      {/* Development-Only Testing Utility */}
      {!isApiMode() && <div className="mt-4 pt-4 border-t border-[#E5EAE7]">
        <button
          type="button"
          onClick={() => setShowDevHelper(!showDevHelper)}
          className="w-full flex items-center justify-between text-[11px] font-semibold text-[#64748B] hover:text-[#182B25] p-1.5 rounded-lg bg-[#F8FAF9] border border-[#E5EAE7]"
        >
          <span className="flex items-center gap-1.5">
            <Code className="h-3.5 w-3.5 text-[#16866A]" />
            <span>Development Testing Utility</span>
          </span>
          <span className="text-[10px] font-mono text-[#94A3B8]">{showDevHelper ? 'Hide ▲' : 'Autofill Demo Accounts ▼'}</span>
        </button>

        {showDevHelper && (
          <div className="mt-2 space-y-1.5 rounded-xl bg-[#F8FAF9] p-2.5 border border-[#E5EAE7] text-left text-[11px]">
            <p className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider mb-1">
              Select Demo Scenario:
            </p>
            {allUsers.map((u) => {
              const isSelected = email === u.email;
              const roleSummary = u.assignedRoles.map((r) => r.replace('_', ' ')).join(' + ');

              return (
                <button
                  key={u.id}
                  type="button"
                  onClick={() => autofillAccount(u.email)}
                  className={`w-full flex items-center justify-between p-2 rounded-lg border text-left transition-colors ${
                    isSelected
                      ? 'border-[#16866A] bg-emerald-50 text-[#16866A] font-bold'
                      : 'border-transparent hover:bg-white text-[#182B25]'
                  }`}
                >
                  <div>
                    <span className="block font-semibold">{u.name}</span>
                    <span className="text-[10px] text-[#64748B]">{roleSummary}</span>
                  </div>
                  {isSelected && <Check className="h-3.5 w-3.5 text-[#16866A]" />}
                </button>
              );
            })}
          </div>
        )}
      </div>}
    </div>
  );
};
