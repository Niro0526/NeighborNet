import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  badge?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  action,
  badge,
}) => {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="flex items-center gap-2.5">
          <h1 className="text-xl md:text-2xl font-extrabold text-[#182B25] tracking-tight">{title}</h1>
          {badge}
        </div>
        {subtitle && <p className="mt-1 text-xs md:text-sm text-[#64748B]">{subtitle}</p>}
      </div>
      {action && <div className="flex items-center gap-2.5">{action}</div>}
    </div>
  );
};
