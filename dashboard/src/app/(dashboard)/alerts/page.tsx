import { prisma } from "@/lib/prisma";
import { formatDistanceToNow } from "date-fns";
import { Bell, ShieldAlert, Filter, Search } from "lucide-react";

export default async function AlertsPage() {
  const alerts = await prisma.alert.findMany({
    orderBy: { createdAt: 'desc' },
    include: { device: true }
  });

  return (
    <div className="space-y-12 max-w-7xl mx-auto font-mono">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-white/20 text-[10px] font-bold uppercase tracking-widest">
          <span>Root</span>
          <span>/</span>
          <span>Alerts</span>
        </div>
        <h2 className="text-4xl font-black tracking-tighter uppercase text-white">Security_Alerts</h2>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-white/10">
        <div className="flex items-center gap-4">
          <div className="text-[10px] font-black uppercase tracking-[0.3em] text-white/20">Alert_Log_v1</div>
          <div className="h-4 w-[1px] bg-white/5" />
          <div className="text-[10px] font-black uppercase tracking-[0.3em] text-accent">{alerts.length}_Active_Threats</div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="relative group">
            <Search className="absolute left-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/20 group-focus-within:text-accent transition-colors" />
            <input 
              type="text" 
              placeholder="FILTER_ALERTS..." 
              className="bg-transparent border-b border-white/10 pl-6 py-2 text-[11px] font-bold uppercase tracking-widest w-48 focus:outline-none focus:border-accent transition-colors placeholder:text-white/10"
            />
          </div>
          <div className="relative flex items-center gap-3">
            <Filter className="w-3.5 h-3.5 text-white/20" />
            <select 
              className="bg-transparent text-[10px] font-black uppercase tracking-widest focus:outline-none cursor-pointer text-white/40 hover:text-white transition-colors appearance-none"
              title="Filter by Severity"
            >
              <option value="ALL" className="bg-black text-white">ALL_SEVERITY</option>
              <option value="HIGH" className="bg-black text-white">HIGH</option>
              <option value="MEDIUM" className="bg-black text-white">MEDIUM</option>
              <option value="LOW" className="bg-black text-white">LOW</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts Grid */}
      <div className="grid grid-cols-1 gap-4">
        {alerts.map((alert) => (
          <div 
            key={alert.id} 
            className="border border-white/10 bg-white/[0.02] p-8 flex flex-col md:flex-row gap-8 group hover:bg-white/[0.04] transition-colors relative"
          >
            <div className="flex-shrink-0">
              <div className="w-12 h-12 flex items-center justify-center border border-white/10 text-accent">
                <ShieldAlert className="w-6 h-6" />
              </div>
            </div>
            
            <div className="flex-1 space-y-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-black text-accent uppercase tracking-widest">
                    [{alert.alertType.replace('_', ' ')}]
                  </span>
                  <div className="h-1 w-1 bg-white/20 rounded-full" />
                  <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">
                    ID: {alert.macAddress || 'SYSTEM'}
                  </span>
                </div>
                <span className="text-[10px] font-bold text-white/20 font-mono">
                  {formatDistanceToNow(alert.createdAt, { addSuffix: true })}
                </span>
              </div>
              <h4 className="text-xl font-black text-white uppercase tracking-tighter group-hover:text-accent transition-colors">
                {alert.subject}
              </h4>
              <p className="text-xs text-white/50 leading-relaxed font-bold">
                {alert.body}
              </p>
            </div>

            <div className="flex-shrink-0 flex items-end">
              <button className="text-[9px] font-black uppercase tracking-[0.2em] px-4 py-2 border border-white/10 hover:border-white transition-colors">
                VIEW_DETAILS
              </button>
            </div>
          </div>
        ))}

        {alerts.length === 0 && (
          <div className="py-32 border border-white/5 bg-white/[0.01] text-center space-y-4">
            <div className="flex justify-center">
              <Bell className="w-12 h-12 text-white/5" />
            </div>
            <p className="text-[11px] font-black uppercase tracking-[0.4em] text-white/10">No_Security_Incidents_Detected</p>
          </div>
        )}
      </div>
    </div>
  );
}
