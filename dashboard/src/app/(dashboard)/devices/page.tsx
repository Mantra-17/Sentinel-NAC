import DeviceTable from "@/components/DeviceTable";
import { prisma } from "@/lib/prisma";

export default async function DevicesPage() {
  const devices = await prisma.device.findMany();

  return (
    <div className="space-y-12 max-w-7xl mx-auto font-mono">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-white/20 text-[10px] font-bold uppercase tracking-widest">
          <span>Root</span>
          <span>/</span>
          <span>Nodes</span>
        </div>
        <h2 className="text-4xl font-black tracking-tighter uppercase text-white">Network_Nodes</h2>
      </div>

      {/* Main Content */}
      <div className="border border-white/5 bg-white/[0.01] p-10">
        <DeviceTable />
      </div>
    </div>
  );
}
