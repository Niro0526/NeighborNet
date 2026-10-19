import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  variant?: 'default' | 'emerald' | 'amber' | 'red' | 'blue';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = 'default',
}) => {
  const variantStyles = {
    default: {
      iconBg: 'bg-slate-100 text-[#182B25]',
      border: 'border-[#E5EAE7]',
    },
    emerald: {
      iconBg: 'bg-emerald-50 text-emerald-700',
      border: 'border-emerald-100',
    },
    amber: {
      iconBg: 'bg-amber-50 text-amber-700',
      border: 'border-amber-100',
    },
    red: {
      iconBg: 'bg-red-50 text-red-700',
      border: 'border-red-100',
    },
    blue: {
      iconBg: 'bg-blue-50 text-blue-700',
      border: 'border-blue-100',
    },
  };

  const currentVariant = variantStyles[variant];

  return (
    <div className={`rounded-2xl bg-white p-5 shadow-xs border ${currentVariant.border} card-hover`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-[#64748B]">{title}</span>
        <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${currentVariant.iconBg}`}>
          <Icon className="h-4.5 w-4.5" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-extrabold text-[#182B25] tracking-tight">{value}</span>
        {trend && (
          <span
            className={`text-xs font-bold ${
              trend.isPositive ? 'text-emerald-700' : 'text-red-600'
            }`}
          >
            {trend.value}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-[11px] text-[#64748B]">{subtitle}</p>}
    </div>
  );
};
