import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserRole } from '../../types';
import { useAuth } from '../../hooks';
import { Building2, Users, HandHeart, ArrowRight } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const { allUsers, switchUser, switchRole } = useAuth();
  const navigate = useNavigate();

  const [selectedRole, setSelectedRole] = useState<UserRole>('FOOD_PROVIDER');
  const [orgName, setOrgName] = useState('Green Oasis Cafe');
  const [contactName, setContactName] = useState('Aravinda Silva');
  const [email, setEmail] = useState('aravinda@greenoasis.lk');
  const [phone, setPhone] = useState('+94 77 999 1234');
  const [address, setAddress] = useState('Galle Road, Moratuwa');

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const matched = allUsers.find((u) => u.assignedRoles.includes(selectedRole));
    if (matched) {
      await switchUser(matched.id);
      await switchRole?.(selectedRole);
    }
    navigate('/dashboard');
  };

  const roleCards: { role: UserRole; title: string; desc: string; icon: React.ComponentType<{ className?: string }> }[] = [
    {
      role: 'FOOD_PROVIDER',
      title: 'Food Provider',
      desc: 'Restaurant, Bakery, Supermarket, Hotel',
      icon: Building2,
    },
    {
      role: 'RECIPIENT',
      title: 'NGO / Recipient',
      desc: 'Community Shelter, Care Home, Relief Hub',
      icon: Users,
    },
    {
      role: 'VOLUNTEER',
      title: 'Volunteer Courier',
      desc: 'Deliver surplus resources with bicycle, motorbike, or car',
      icon: HandHeart,
    },
  ];

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold tracking-tight text-[#182B25]">Create Account</h2>
        <p className="mt-1 text-xs text-[#64748B]">
          Join NeighborNet AI to coordinate surplus resources in Sri Lanka.
        </p>
      </div>

      <form onSubmit={handleRegister} className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-[#182B25] mb-2">Select Your Role</label>
          <div className="grid grid-cols-2 gap-2">
            {roleCards.map((rc) => {
              const Icon = rc.icon;
              return (
                <button
                  key={rc.role}
                  type="button"
                  onClick={() => setSelectedRole(rc.role)}
                  className={`rounded-xl p-3 border text-left transition-all ${
                    selectedRole === rc.role
                      ? 'border-[#16866A] bg-emerald-50/60 ring-1 ring-[#16866A]'
                      : 'border-[#E5EAE7] bg-[#F8FAF9] hover:bg-slate-100'
                  }`}
                >
                  <Icon className={`h-4 w-4 mb-1.5 ${selectedRole === rc.role ? 'text-[#16866A]' : 'text-[#64748B]'}`} />
                  <p className="text-xs font-bold text-[#182B25]">{rc.title}</p>
                  <p className="text-[10px] text-[#64748B] line-clamp-1">{rc.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {selectedRole !== 'VOLUNTEER' && (
          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Organization Name</label>
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              required
              className="w-full rounded-xl border border-[#E5EAE7] bg-white px-3.5 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-bold text-[#182B25] mb-1">Contact Person Name</label>
          <input
            type="text"
            value={contactName}
            onChange={(e) => setContactName(e.target.value)}
            required
            className="w-full rounded-xl border border-[#E5EAE7] bg-white px-3.5 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-xl border border-[#E5EAE7] bg-white px-3.5 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-[#182B25] mb-1">Phone (+94)</label>
            <input
              type="text"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
              className="w-full rounded-xl border border-[#E5EAE7] bg-white px-3.5 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-[#182B25] mb-1">Address / Hub Location</label>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            required
            className="w-full rounded-xl border border-[#E5EAE7] bg-white px-3.5 py-2 text-xs text-[#182B25] focus:border-[#16866A] focus:outline-none"
          />
        </div>

        <button
          type="submit"
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-[#16866A] py-2.5 px-4 text-xs font-bold text-white shadow-xs hover:bg-[#09664F] transition-all cursor-pointer"
        >
          <span>Complete Demo Registration</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </form>

      <div className="mt-4 flex items-center justify-center gap-2 text-xs text-[#64748B]">
        <span>Already have an account?</span>
        <Link to="/login" className="font-bold text-[#16866A] hover:underline">
          Sign In
        </Link>
      </div>
    </div>
  );
};
