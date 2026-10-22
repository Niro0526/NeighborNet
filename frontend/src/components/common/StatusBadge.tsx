import React from 'react';

export type StatusBadgeVariant =
  | 'available'
  | 'reserved'
  | 'collected'
  | 'expired'
  | 'withdrawn'
  | 'pending'
  | 'allocated'
  | 'fulfilled'
  | 'critical'
  | 'urgent'
  | 'high'
  | 'medium'
  | 'low'
  | 'active'
  | 'offline'
  | 'busy'
  | 'delivered'
  | 'disrupted';

interface StatusBadgeProps {
  status: string;
  variant?: StatusBadgeVariant;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant,
  size = 'md',
}) => {
  const normalized = (variant || status).toLowerCase() as StatusBadgeVariant;

  const styleMap: Record<string, string> = {
    available: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    delivered: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    fulfilled: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    active: 'bg-emerald-50 text-emerald-700 border-emerald-200',

    reserved: 'bg-amber-50 text-amber-700 border-amber-200',
    pending: 'bg-amber-50 text-amber-700 border-amber-200',
    medium: 'bg-amber-50 text-amber-700 border-amber-200',
    busy: 'bg-amber-50 text-amber-700 border-amber-200',

    collected: 'bg-blue-50 text-blue-700 border-blue-200',
    allocated: 'bg-blue-50 text-blue-700 border-blue-200',

    critical: 'bg-red-50 text-red-700 border-red-200',
    urgent: 'bg-red-50 text-red-700 border-red-200',
    high: 'bg-orange-50 text-orange-700 border-orange-200',
    expired: 'bg-red-50 text-red-700 border-red-200',
    withdrawn: 'bg-slate-50 text-slate-600 border-slate-200',
    disrupted: 'bg-red-50 text-red-700 border-red-200',

    low: 'bg-slate-50 text-slate-700 border-slate-200',
    offline: 'bg-slate-50 text-slate-700 border-slate-200',
  };

  const badgeStyle = styleMap[normalized] || 'bg-slate-50 text-slate-700 border-slate-200';
  const sizeStyle = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center rounded-lg border font-semibold capitalize ${badgeStyle} ${sizeStyle}`}
    >
      {status.replace('_', ' ')}
    </span>
  );
};
