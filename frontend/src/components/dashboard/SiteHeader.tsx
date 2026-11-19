import { useLocation } from 'react-router-dom';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SiteHeaderProps {
    onRefresh?: () => void;
    isRefreshing?: boolean;
}

const pageTitles: Record<string, string> = {
    '/dashboard': 'Security Dashboard',
    '/dashboard/tests': 'Penetration Tests',
    '/dashboard/issues': 'Issues',
    '/dashboard/chats': 'Chats',
    '/dashboard/monitor': 'Event Monitor',
    '/dashboard/settings': 'Settings',
    '/dashboard/status': 'Status',
    '/dashboard/findings': 'Findings',
    '/dashboard/targets': 'Target Inventory',
};

export function SiteHeader({ onRefresh, isRefreshing }: SiteHeaderProps) {
    const location = useLocation();

    // Match the most specific path first
    const title =
        Object.entries(pageTitles)
            .sort(([a], [b]) => b.length - a.length)
            .find(([path]) =>
            location.pathname === path || location.pathname.startsWith(path + '/')
        )?.[1] ?? 'Dashboard';

    return (
        // Claudin titlebar: 32px, bg-elevated, crumbs "fennec / <page>", actions on the right.
        <header className="sticky top-0 z-10 flex h-titlebar shrink-0 items-center border-b bg-ds-elevated select-none">
            <div className="flex w-full min-w-0 items-center gap-[7px] pl-2 pr-2">
                <SidebarTrigger className="h-6 w-6 text-ds-tertiary hover:text-ds-fg" />
                <Separator
                    orientation="vertical"
                    className="mx-1 data-[orientation=vertical]:h-3.5"
                />
                <span className="text-xs font-semibold tracking-[0.02em] text-ds-fg">fennec</span>
                <span className="text-ds-quaternary">/</span>
                <h1 className="min-w-0 truncate text-xs font-normal text-ds-fg-muted">{title}</h1>

                {onRefresh && (
                    <div className="ml-auto flex items-center gap-1.5">
                        <Button
                            size="sm"
                            onClick={onRefresh}
                            disabled={isRefreshing}
                        >
                            <RefreshCw
                                className={cn('h-3 w-3', isRefreshing && 'animate-spin')}
                            />
                            <span className="hidden sm:inline">Refresh</span>
                        </Button>
                    </div>
                )}
            </div>
        </header>
    );
}