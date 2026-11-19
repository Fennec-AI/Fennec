import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Activity,
    ShieldAlert,
    Globe,
    Plus,
    MessageCircle,
} from 'lucide-react';
import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from '@/components/ui/sidebar';
import { useState } from "react";
import { TestDialog } from "@/components/dashboard/TestDialogBox.tsx";

/* ------------------------------------------------------------------ */
/*  Navigation data                                                    */
/* ------------------------------------------------------------------ */

const navMain = [
    { title: 'Overview', href: '/dashboard', icon: LayoutDashboard },
    { title: 'Status', href: '/dashboard/status', icon: Activity },
    { title: 'Findings', href: '/dashboard/findings', icon: ShieldAlert },
    { title: 'Target Inventory', href: '/dashboard/targets', icon: Globe },
    { title: 'AI Chat', href: '/dashboard/chats', icon: MessageCircle },
];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
    const location = useLocation();
    const navigate = useNavigate();
    const [TestOpen, setTestOpen] = useState(false);

    const isActive = (href: string) => {
        if (href === '/dashboard') return location.pathname === '/dashboard';
        return location.pathname.startsWith(href);
    };

    return (
        <>
        <Sidebar collapsible="icon" {...props}>
            {/* ---- Header / Logo ---- */}
            <SidebarHeader className="h-titlebar justify-center border-b bg-ds-elevated px-2 py-0">
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton
                            asChild
                            className="h-6 hover:bg-transparent"
                        >
                            <Link to="/dashboard">
                                <img
                                    src="/fennec.png"
                                    alt="Fennec"
                                    className="h-4 w-4 rounded-[4px] object-contain"
                                />
                                <span className="text-xs font-semibold tracking-[0.02em]">fennec</span>
                            </Link>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>

            {/* ---- Main content ---- */}
            <SidebarContent>
                {/* Quick action */}
                <SidebarGroup>
                    <SidebarGroupContent className="flex flex-col gap-2">
                        <SidebarMenu>
                            <SidebarMenuItem>
                                <SidebarMenuButton
                                    tooltip="Create"
                                    onClick={() => setTestOpen(true)}
                                    className="h-control min-w-8 justify-center border border-border bg-ds-sunken text-[11px] font-semibold text-ds-fg-muted hover:border-ds-border-strong hover:bg-ds-panel-hover hover:text-ds-fg active:bg-ds-panel-hover"
                                >
                                    <Plus className="h-3.5 w-3.5" />
                                    <span>Create</span>
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>

                {/* Platform nav */}
                <SidebarGroup>
                    <SidebarGroupLabel>Platform</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {navMain.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton
                                        tooltip={item.title}
                                        isActive={isActive(item.href)}
                                        onClick={() => navigate(item.href)}
                                        className="cursor-pointer"
                                    >
                                        <item.icon className="h-3.5 w-3.5" />
                                        <span>{item.title}</span>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
        </Sidebar>
        <TestDialog open={TestOpen} onOpenChange={setTestOpen} />
        </>
    );
}
