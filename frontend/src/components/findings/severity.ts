export const severityStyle: Record<string, string> = {
  critical: 'border-red-500/40 bg-red-500/15 text-red-400',
  high: 'border-orange-500/40 bg-orange-500/15 text-orange-400',
  medium: 'border-yellow-500/40 bg-yellow-500/15 text-yellow-400',
  low: 'border-green-500/40 bg-green-500/15 text-green-400',
  info: 'border-fennec-dark-600 bg-fennec-dark-800 text-fennec-dark-300',
};

export function severityClass(level: string): string {
  return severityStyle[level.toLowerCase()] || severityStyle.info;
}
