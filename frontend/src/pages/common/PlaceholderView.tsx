import React from 'react';
import { PageHeader } from '../../components/common/PageHeader';
import { Link } from 'react-router-dom';
import { Layers, ArrowLeft } from 'lucide-react';

interface PlaceholderViewProps {
  title: string;
  subtitle: string;
  backPath?: string;
}

export const PlaceholderView: React.FC<PlaceholderViewProps> = ({
  title,
  subtitle,
  backPath,
}) => {
  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        subtitle={subtitle}
        action={
          backPath ? (
            <Link
              to={backPath}
              className="flex items-center gap-1.5 rounded-xl border border-[#E5EAE7] bg-white px-3 py-1.5 text-xs font-semibold text-[#64748B] hover:bg-[#F8FAF9]"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back</span>
            </Link>
          ) : undefined
        }
      />

      <div className="rounded-3xl border border-dashed border-[#E5EAE7] bg-white p-12 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-[#16866A] mb-4">
          <Layers className="h-7 w-7" />
        </div>
        <h3 className="text-base font-bold text-[#182B25]">{title}</h3>
        <p className="mt-1 text-xs text-[#64748B] max-w-md mx-auto leading-relaxed">
          {subtitle}. This view connects with centralized mock repository services and will be fully expanded in Phase 2 & 3.
        </p>
        <div className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#F8FAF9] px-4 py-2 border border-[#E5EAE7] text-xs font-semibold text-[#16866A]">
          <span>Service Endpoint: Active In-Memory Mock Store</span>
        </div>
      </div>
    </div>
  );
};
