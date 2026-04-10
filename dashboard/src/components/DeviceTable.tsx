"use client";

import { useState, useEffect } from "react";
import { 
  MoreVertical, 
  Search,
  Filter,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  ShieldBan,
  Trash2,
  Loader2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { updateDeviceStatus, getDevices, deleteDevice } from "@/app/actions/device-actions";
import { useSession } from "next-auth/react";

export default function DeviceTable() {
  const { data: session, status: authStatus } = useSession();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const isAdmin = (session?.user as any)?.role === "admin" || (session?.user as any)?.role === "superadmin";

  useEffect(() => {
    if (authStatus !== "loading") {
      loadDevices();
    }
  }, [authStatus]);

  async function loadDevices() {
    setLoading(true);
    try {
      const data = await getDevices();
      setDevices(data);
    } catch (error) {
      console.error("Failed to load devices", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleStatusChange(id: number, status: string) {
    setUpdatingId(id);
    try {
      await updateDeviceStatus(id, status as any);
      await loadDevices();
    } catch (error) {
      console.error("Failed to update status", error);
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Are you sure you want to clear this entry? The device will be forgotten and re-discovered as new.")) return;
    setUpdatingId(id);
    try {
      await deleteDevice(id);
      await loadDevices();
    } catch (error) {
      console.error("Failed to delete device", error);
    } finally {
      setUpdatingId(null);
    }
  }

  const filteredDevices = devices.filter((d) => {
    const matchesSearch = 
      d.macAddress.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (d.ipAddress?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false) ||
      (d.hostname?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false) ||
      (d.vendor?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
    
    const matchesStatus = statusFilter === "ALL" || d.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 font-mono">
      {/* Search & Filter Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-white/10">
        <div className="flex items-center gap-4">
          <div className="text-[10px] font-black uppercase tracking-[0.3em] text-white/20">Registry_v1</div>
          <div className="h-4 w-[1px] bg-white/5" />
          <div className="text-[10px] font-black uppercase tracking-[0.3em] text-accent">Active_Nodes</div>
          {isAdmin && (
            <div className="ml-4 px-2 py-0.5 border border-accent/20 bg-accent/5 text-[8px] font-black text-accent uppercase tracking-widest flex items-center gap-1.5">
              <div className="w-1 h-1 bg-accent rounded-full animate-pulse" />
              Admin_Mode
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-6">
          <div className="relative group">
            <Search className="absolute left-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/20 group-focus-within:text-accent transition-colors" />
            <input 
              type="text" 
              placeholder="SEARCH_QUERY..." 
              className="bg-transparent border-b border-white/10 pl-6 py-2 text-[11px] font-bold uppercase tracking-widest w-48 focus:outline-none focus:border-accent transition-colors placeholder:text-white/10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="relative flex items-center gap-3">
            <Filter className="w-3.5 h-3.5 text-white/20" />
            <select 
              className="bg-transparent text-[10px] font-black uppercase tracking-widest focus:outline-none cursor-pointer text-white/40 hover:text-white transition-colors appearance-none"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              title="Filter by Status"
            >
              <option value="ALL" className="bg-black text-white">ALL_NODES</option>
              <option value="ALLOWED" className="bg-black text-white">ALLOWED</option>
              <option value="BLOCKED" className="bg-black text-white">BLOCKED</option>
              <option value="QUARANTINED" className="bg-black text-white">QUARANTINED</option>
              <option value="UNKNOWN" className="bg-black text-white">UNKNOWN</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="border border-white/10 bg-white/[0.01] overflow-x-auto overflow-y-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-white/10 text-[9px] font-black uppercase tracking-[0.2em] text-white/20">
              <th className="px-4 py-5">MAC ADDRESS</th>
              <th className="px-4 py-5">IP ADDRESS</th>
              <th className="px-4 py-5">HOSTNAME</th>
              <th className="px-4 py-5">VENDOR</th>
              <th className="px-4 py-5">OS (EST.)</th>
              <th className="px-4 py-5">STATUS</th>
              <th className="px-4 py-5">LAST SEEN</th>
              {isAdmin && <th className="px-4 py-5 text-right">ACTIONS</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {loading ? (
              <tr>
                <td colSpan={isAdmin ? 8 : 7} className="px-8 py-20 text-center">
                  <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-6 h-6 text-accent animate-spin" />
                    <p className="text-[10px] font-black uppercase tracking-[0.4em] text-white/20">Syncing_Records...</p>
                  </div>
                </td>
              </tr>
            ) : filteredDevices.map((device) => (
              <tr key={device.id} className="hover:bg-white/[0.03] transition-colors group">
                <td className="px-4 py-5">
                  <p className="text-[11px] font-black text-rose-400/80 group-hover:text-rose-400 transition-colors">{device.macAddress}</p>
                </td>
                <td className="px-4 py-5 text-white/60">
                  <p className="text-[11px] font-bold">{device.ipAddress || '---'}</p>
                </td>
                <td className="px-4 py-5 text-white/60">
                  <p className="text-[11px] font-bold">{device.hostname || '---'}</p>
                </td>
                <td className="px-4 py-5 text-white/60">
                  <p className="text-[10px] font-bold">{device.vendor || '---'}</p>
                </td>
                <td className="px-4 py-5 text-white/40">
                  <p className="text-[10px] font-bold">{device.probableOs || '---'}</p>
                </td>
                <td className="px-4 py-5">
                  <div className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded-full border text-[8px] font-black uppercase tracking-widest",
                    device.status === 'ALLOWED' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500' :
                    device.status === 'BLOCKED' ? 'bg-rose-500/10 border-rose-500/20 text-rose-500' :
                    device.status === 'QUARANTINED' ? 'bg-amber-500/10 border-amber-500/20 text-amber-500' : 
                    'bg-blue-500/10 border-blue-500/20 text-blue-500'
                  )}>
                    {device.status}
                  </div>
                </td>
                <td className="px-4 py-5 text-white/40">
                  <p className="text-[9px] font-bold uppercase tracking-widest">
                    {formatDistanceToNow(new Date(device.lastSeen), { addSuffix: true })}
                  </p>
                </td>
                {isAdmin && (
                  <td className="px-4 py-5 text-right">
                    <div className="flex items-center justify-end">
                      {updatingId === device.id ? (
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-3.5 h-3.5 text-emerald-500 animate-spin" />
                          <span className="text-[8px] font-black uppercase tracking-widest text-emerald-500/50 animate-pulse">PROCESSING...</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          {/* ALLOW */}
                          <button 
                            onClick={() => handleStatusChange(device.id, 'ALLOWED')}
                            disabled={device.status === 'ALLOWED'}
                            className={cn(
                              "p-2.5 rounded-lg transition-all border shadow-sm group/btn",
                              device.status === 'ALLOWED' 
                                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500/30 cursor-not-allowed opacity-50" 
                                : "bg-emerald-500/5 border-emerald-500/10 text-emerald-500/40 hover:bg-emerald-500/20 hover:border-emerald-500/40 hover:text-emerald-400 hover:shadow-emerald-500/10"
                            )}
                            title="ALLOW_ACCESS"
                          >
                            <ShieldCheck className="w-4 h-4" />
                          </button>

                          {/* QUARANTINE */}
                          <button 
                            onClick={() => handleStatusChange(device.id, 'QUARANTINED')}
                            disabled={device.status === 'QUARANTINED'}
                            className={cn(
                              "p-2.5 rounded-lg transition-all border shadow-sm",
                              device.status === 'QUARANTINED' 
                                ? "bg-amber-500/10 border-amber-500/20 text-amber-500/30 cursor-not-allowed opacity-50" 
                                : "bg-amber-500/5 border-amber-500/10 text-amber-500/40 hover:bg-amber-500/20 hover:border-amber-500/40 hover:text-amber-400 hover:shadow-amber-500/10"
                            )}
                            title="QUARANTINE"
                          >
                            <ShieldAlert className="w-4 h-4" />
                          </button>
                          
                          {/* BLOCK */}
                          <button 
                            onClick={() => handleStatusChange(device.id, 'BLOCKED')}
                            disabled={device.status === 'BLOCKED'}
                            className={cn(
                              "p-2.5 rounded-lg transition-all border shadow-sm",
                              device.status === 'BLOCKED' 
                                ? "bg-rose-500/10 border-rose-500/20 text-rose-500/30 cursor-not-allowed opacity-50" 
                                : "bg-rose-500/5 border-rose-500/10 text-rose-500/40 hover:bg-rose-500/20 hover:border-rose-500/40 hover:text-rose-400 hover:shadow-rose-500/10"
                            )}
                            title="BLOCK_DEVICE"
                          >
                            <ShieldBan className="w-4 h-4" />
                          </button>

                          {/* FORGET / CLEAR ENTRY */}
                          <button 
                            onClick={() => handleDelete(device.id)}
                            className="p-2.5 rounded-lg bg-white/5 border border-white/10 text-white/20 hover:bg-white/10 hover:border-white/20 hover:text-white transition-all shadow-sm hover:shadow-white/5"
                            title="FORGET_DEVICE (CLEARS ENTRY)"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        
        {!loading && filteredDevices.length === 0 && (
          <div className="p-20 text-center space-y-4">
            <p className="text-[10px] font-black text-white/10 uppercase tracking-[0.4em]">NO_RECORDS_FOUND</p>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-[9px] font-black uppercase tracking-[0.2em] text-white/20">
        <p>PAGE_01 // {filteredDevices.length}_RECORDS</p>
        <div className="flex gap-8">
          <button className="hover:text-white transition-colors disabled:opacity-10" disabled>PREV_PAGE</button>
          <button className="hover:text-white transition-colors disabled:opacity-10" disabled>NEXT_PAGE</button>
        </div>
      </div>
    </div>
  );
}
