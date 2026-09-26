import type { Severity } from '../data/mockAnalysis';

const config: Record<Severity, { label: string; bg: string; text: string; dot: string }> = {
  critical: { label: 'CRITICAL', bg: 'bg-[#FFF1F1]', text: 'text-[#DA1E28]', dot: 'bg-[#DA1E28]' },
  high:     { label: 'HIGH',     bg: 'bg-[#FFF1F1]', text: 'text-[#DA1E28]', dot: 'bg-[#DA1E28]' },
  medium:   { label: 'MEDIUM',   bg: 'bg-[#FDF6DD]', text: 'text-[#8A6400]', dot: 'bg-[#F1C21B]' },
  low:      { label: 'LOW',      bg: 'bg-[#F4F4F4]', text: 'text-[#525252]', dot: 'bg-[#8D8D8D]' },
};

interface Props {
  severity: Severity;
  size?: 'sm' | 'md';
}

export default function SeverityBadge({ severity, size = 'md' }: Props) {
  const c = config[severity];
  const textSize = size === 'sm' ? 'text-[10px]' : 'text-xs';
  const px = size === 'sm' ? 'px-1.5 py-0.5' : 'px-2 py-1';
  return (
    <span className={`inline-flex items-center gap-1.5 font-mono font-medium ${textSize} ${px} ${c.bg} ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}
