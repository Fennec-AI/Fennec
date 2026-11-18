export const severityStyle: Record<string, string> = {
  // Claudin: status color stays small — colored text and outline, no fills.
  critical: 'border-red-500/40 bg-transparent text-red-400',
  high: 'border-orange-500/40 bg-transparent text-orange-400',
  medium: 'border-yellow-500/40 bg-transparent text-yellow-400',
  low: 'border-green-500/40 bg-transparent text-green-400',
  info: 'border-border bg-transparent text-ds-tertiary',
};

export function severityClass(level: string): string {
  return severityStyle[level.toLowerCase()] || severityStyle.info;
}
