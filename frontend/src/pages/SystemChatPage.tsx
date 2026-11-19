import DashboardLayout from '@/components/dashboard/DashboardLayout';
import ContextChat from '@/components/chat/ContextChat';

export default function SystemChatPage() {
  return <DashboardLayout><div className="mx-auto w-full max-w-4xl space-y-4 p-4 lg:p-6">
    <div><h1 className="text-lg font-semibold">Chat geral com a IA</h1>
      <p className="text-sm text-muted-foreground">Converse sobre assessments, hipóteses e descobertas do sistema.</p></div>
    <ContextChat scope="system" contextId="all" title="Sistema Fennec" />
  </div></DashboardLayout>;
}
