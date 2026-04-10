import Sidebar from "@/components/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-black text-white selection:bg-accent selection:text-black">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-white/5 bg-black/50 backdrop-blur-sm flex items-center justify-between px-10 sticky top-0 z-10">
          <div className="flex items-center gap-4 text-[10px] font-black uppercase tracking-[0.2em]">
            <span className="text-white/20">System</span>
            <span className="text-white/10">/</span>
            <span className="text-white">Active_Monitor</span>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]" />
              <span className="text-[9px] font-black text-accent uppercase tracking-widest">Link_Established</span>
            </div>
            <div className="h-4 w-[1px] bg-white/10" />
            <span className="text-[9px] text-white/20 font-mono font-bold">
              {new Date().toISOString().replace('T', ' ').substring(0, 19)}
            </span>
          </div>
        </header>
        <div className="flex-1 p-10 relative overflow-y-auto">
          <div className="scanline" />
          {children}
        </div>
      </main>
    </div>
  );
}
