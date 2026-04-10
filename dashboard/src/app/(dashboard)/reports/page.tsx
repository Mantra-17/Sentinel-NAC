import { prisma } from "@/lib/prisma";
import { formatDistanceToNow } from "date-fns";
import { FileBarChart, Terminal, Search, Download } from "lucide-react";
import ReportDownloadButton from "@/components/ReportDownloadButton";

export default async function ReportsPage() {
  const events = await prisma.deviceEvent.findMany({
    take: 100,
    orderBy: { createdAt: 'desc' },
  });

  return (
    <div className="space-y-12 max-w-7xl mx-auto font-mono">
      {/* Header */}
      <div className="flex items-end justify-between border-b border-white/10 pb-12">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-white/20 text-[10px] font-bold uppercase tracking-widest">
            <span>Root</span>
            <span>/</span>
            <span>Logs</span>
          </div>
          <h2 className="text-4xl font-black tracking-tighter uppercase text-white">System_Logs</h2>
        </div>
        
        <ReportDownloadButton 
          data={events} 
          title="Security Event Logs" 
          filename="sentinel_event_logs" 
        />
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6">
        <div className="flex items-center gap-4">
          <div className="text-[10px] font-black uppercase tracking-[0.3em] text-white/20">Event_Log_v1</div>
          <div className="h-4 w-[1px] bg-white/5" />
          <div className="text-[10px] font-black uppercase tracking-[0.3em] text-accent">{events.length}_Stored_Entries</div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="relative group">
            <Search className="absolute left-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/20 group-focus-within:text-accent transition-colors" />
            <input 
              type="text" 
              placeholder="SEARCH_LOGS..." 
              className="bg-transparent border-b border-white/10 pl-6 py-2 text-[11px] font-bold uppercase tracking-widest w-48 focus:outline-none focus:border-accent transition-colors placeholder:text-white/10"
            />
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="border border-white/10 bg-white/[0.01]">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-white/10 text-[9px] font-black uppercase tracking-[0.2em] text-white/20">
              <th className="px-8 py-5">Event_Type</th>
              <th className="px-8 py-5">Node_ID</th>
              <th className="px-8 py-5">Action_Details</th>
              <th className="px-8 py-5">Actor</th>
              <th className="px-8 py-5 text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {events.map((event) => (
              <tr key={event.id} className="hover:bg-white/[0.03] transition-colors group">
                <td className="px-8 py-5">
                  <span className="text-[10px] font-black text-accent uppercase tracking-widest">
                    [{event.eventType}]
                  </span>
                </td>
                <td className="px-8 py-5">
                  <p className="text-[11px] font-black text-white">{event.macAddress}</p>
                </td>
                <td className="px-8 py-5">
                  <p className="text-[11px] font-bold text-white/40">{event.details || 'N/A'}</p>
                </td>
                <td className="px-8 py-5">
                  <p className="text-[11px] font-bold text-white/40 uppercase">{event.actor || 'SYSTEM'}</p>
                </td>
                <td className="px-8 py-5 text-right">
                  <p className="text-[10px] font-bold text-white/20 font-mono">
                    {formatDistanceToNow(event.createdAt, { addSuffix: true })}
                  </p>
                </td>
              </tr>
            ))}
            {events.length === 0 && (
              <tr>
                <td colSpan={5} className="px-8 py-20 text-center">
                  <div className="flex flex-col items-center gap-4">
                    <Terminal className="w-6 h-6 text-white/10" />
                    <p className="text-[10px] font-black uppercase tracking-[0.4em] text-white/10">No_Events_Recorded</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
