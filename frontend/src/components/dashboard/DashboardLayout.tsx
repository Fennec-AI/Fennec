import { ReactNode } from 'react';
import {AppSidebar} from "@/components/dashboard/AppSideBar.tsx";
import { SiteHeader } from './SiteHeader';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

interface DashboardLayoutProps {
    children: ReactNode;
    fitViewport?: boolean;
    onRefresh?: () => void;
    isRefreshing?: boolean;
}

export default function DashboardLayout({
                                            children,
                                            fitViewport = false,
                                            onRefresh,
                                            isRefreshing,
                                        }: DashboardLayoutProps) {
    return (
        <SidebarProvider
            className={fitViewport ? "h-dvh min-h-0 overflow-hidden" : undefined}
            style={
                {
                    // Claudin sizes: sidebar-width 224px, titlebar-height 32px
                    '--sidebar-width': '224px',
                    '--header-height': '32px',
                } as React.CSSProperties
            }
        >
            <AppSidebar/>
            {/*
              `min-w-0 overflow-x-hidden` is load-bearing: without it, any
              long unbreakable string inside the page (e.g. a recon command
              with a long URL, a pre/code block) blows out the flex child,
              `SidebarInset` grows past the viewport, and the page content
              slides under the fixed sidebar. Reported as the "sidebar
              randomly takes off" flake.
            */}
            <SidebarInset className={`min-w-0 overflow-x-hidden ${fitViewport ? "min-h-0 overflow-y-hidden" : ""}`}>
                <SiteHeader onRefresh={onRefresh} isRefreshing={isRefreshing} />
                <div className="flex min-h-0 min-w-0 flex-1 flex-col">
                    <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-2">
                        {children}
                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
}