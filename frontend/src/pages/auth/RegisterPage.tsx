import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';
import { useAuth } from '../../hooks';

export function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const input = 'mt-1 w-full rounded-xl border border-[#E5EAE7] px-3 py-2 text-sm';
  return <div><h2 className="text-2xl font-bold">Create account</h2><p className="mt-2 text-sm text-slate-600">Receive surplus food as an individual. An organization is optional.</p>
    <form className="mt-5 space-y-4" onSubmit={async e => {
      e.preventDefault(); setBusy(true); setError('');
      try {
        await authService.register({ email, password, full_name: name, phone, roles: role ? [role] : [] });
        await login({ email, password });
        navigate('/community-food');
      } catch (e: any) { setError(e.message || 'Registration failed.'); } finally { setBusy(false); }
    }}>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <label className="block text-sm">Full name<input autoComplete="name" className={input} required value={name} onChange={e => setName(e.target.value)} /></label>
      <label className="block text-sm">Email<input autoComplete="email" className={input} type="email" required value={email} onChange={e => setEmail(e.target.value)} /></label>
      <label className="block text-sm">Phone<input autoComplete="tel" className={input} value={phone} onChange={e => setPhone(e.target.value)} /></label>
      <label className="block text-sm">Password<input autoComplete="new-password" className={input} type="password" minLength={8} required value={password} onChange={e => setPassword(e.target.value)} /></label>
      <label className="block text-sm">Account purpose<select className={input} value={role} onChange={e => setRole(e.target.value)}><option value="">Individual - receive food</option><option value="RECIPIENT">NGO / organization recipient</option><option value="FOOD_PROVIDER">Food provider</option><option value="VOLUNTEER">Volunteer courier</option></select></label>
      {role && <p className="text-xs text-slate-500">Organization membership or courier verification is required for organization operations and deliveries. You can receive food personally immediately.</p>}
      <button disabled={busy} className="w-full rounded-xl bg-[#16866A] p-3 font-semibold text-white disabled:opacity-50">{busy ? 'Creating account...' : 'Create account'}</button>
    </form><p className="mt-4 text-sm">Already registered? <Link className="text-[#16866A]" to="/login">Sign in</Link></p>
  </div>;
}
