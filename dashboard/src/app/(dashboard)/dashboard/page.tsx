import {
  ArrowUpRight,
  ShieldAlert,
  Terminal,
  Cpu,
  Database,
  Globe
} from "lucide-react";
import { cn } from "@/lib/utils";
import DeviceTable from "@/components/DeviceTable";
import { formatDistanceToNow } from "date-fns";
import { prisma } from "@/lib/prisma";

export default async function DashboardPage() {
  const devices = await prisma.device.findMany();
  const alerts = await prisma.alert.findMany({
    take: 5,
    orderBy: { createdAt: 'desc' },
    include: { device: true }
  });

  const counts = {
    total: devices.length,
    allowed: devices.filter(d => d.status === 'ALLOWED').length,
    quarantined: devices.filter(d => d.status === 'QUARANTINED').length,
    blocked: devices.filter(d => d.status === 'BLOCKED').length,
    unknown: devices.filter(d => d.status === 'UNKNOWN').length,
  };

  const stats = [
    { label: "Nodes_Total", value: counts.total },
    { label: "Nodes_Secure", value: counts.allowed },
    { label: "Nodes_Quar", value: counts.quarantined },
    { label: "Nodes_Blocked", value: counts.blocked },
    { label: "Nodes_Unknown", value: counts.unknown },
  ];

  return (
    <div className="space-y-12 max-w-[1400px] mx-auto font-mono">
      {/* Header with breadcrumbs feel */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-white/20 text-[10px] font-bold uppercase tracking-widest">
          <span>Root</span>
          <span>/</span>
          <span>Dashboard</span>
        </div>
        <h2 className="text-4xl font-black tracking-tighter uppercase text-white">System_Overview</h2>
      </div>

      {/* Stark Stat Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 border border-white/10 divide-x divide-white/10 bg-white/[0.02]">
        {stats.map((stat) => (
          <div key={stat.label} className="p-8 space-y-2 group hover:bg-white/5 transition-colors">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-white/30 group-hover:text-accent transition-colors">
              {stat.label}
            </p>
            <p className="text-3xl font-black tracking-tighter text-white">
              {stat.value.toString().padStart(4, '0')}
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main Feed */}
        <div className="lg:col-span-3">
          <DeviceTable />
        </div>

        {/* Sidebar Diagnostics */}
        <div className="space-y-10">
          {/* Priority Alerts */}
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-accent" />
                <h3 className="text-[11px] font-black uppercase tracking-[0.2em]">Priority_Alerts</h3>
              </div>
              <span className="text-[9px] font-bold text-white/20 font-mono">LIVE_FEED</span>
            </div>

            <div className="space-y-6">
              {alerts.map((alert) => (
                <div key={alert.id} className="space-y-1.5 group cursor-pointer">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-black text-accent uppercase tracking-widest">
                      [{alert.alertType.replace('_', ' ')}]
                    </span>
                    <span className="text-[9px] font-bold text-white/10">
                      {formatDistanceToNow(alert.createdAt, { addSuffix: true })}
                    </span>
                  </div>
                  <p className="text-[11px] font-bold text-white/70 group-hover:text-white transition-colors leading-tight">
                    {alert.subject}
                  </p>
                  <p className="text-[9px] text-white/20 font-mono uppercase">
                    ID: {alert.macAddress || 'SYSTEM'}
                  </p>
                </div>
              ))}
              {alerts.length === 0 && (
                <div className="text-[10px] text-white/20 uppercase tracking-widest text-center py-10">
                  NO_ALERTS_LOGGED
                </div>
              )}
            </div>
          </div>

          {/* System Metrics */}
          <div className="space-y-6 pt-4">
            <div className="flex items-center gap-2 border-b border-white/10 pb-4">
              <Terminal className="w-4 h-4 text-white/30" />
              <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-white/40">Diagnostics</h3>
            </div>

            <div className="space-y-5">
              <MetricRow icon={Cpu} label="CPU_LOAD" value="12.4%" progress={12.4} />
              <MetricRow icon={Database} label="MEM_USED" value="45.2%" progress={45.2} />
              <MetricRow icon={Globe} label="NET_TRAF" value="2.8GB/s" progress={65} />
            </div>
          </div>

          {/* Technical Info Box */}
          <div className="p-6 border border-white/10 bg-white/[0.02] space-y-3">
            <div className="flex items-center gap-2 text-[9px] font-black text-white/20 uppercase tracking-widest">
              <div className="w-1 h-1 bg-accent" />
              Environment_Info
            </div>
            <div className="text-[9px] font-bold text-white/40 font-mono leading-relaxed uppercase">
              Node: SGP-SEC-01<br />
              Kernel: 5.15.0-88-GENERIC<br />
              Uptime: 142D 12H 42M
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricRow({ icon: Icon, label, value, progress }: any) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-[9px] font-black uppercase tracking-widest">
        <div className="flex items-center gap-2 text-white/30">
          <Icon className="w-3 h-3" />
          <span>{label}</span>
        </div>
        <span className="text-accent">{value}</span>
      </div>
      <div className="h-[2px] w-full bg-white/5 relative">
        <div
          className="h-full bg-accent absolute top-0 left-0 transition-all duration-1000"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
