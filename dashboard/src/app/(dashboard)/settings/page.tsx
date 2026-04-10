import { prisma } from "@/lib/prisma";
import { Settings, Shield, Terminal, Database, Globe } from "lucide-react";

export default async function SettingsPage() {
  const settings = await prisma.systemSetting.findMany();

  return (
    <div className="space-y-12 max-w-7xl mx-auto font-mono">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-white/20 text-[10px] font-bold uppercase tracking-widest">
          <span>Root</span>
          <span>/</span>
          <span>System</span>
        </div>
        <h2 className="text-4xl font-black tracking-tighter uppercase text-white">System_Configuration</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        {/* Network Settings */}
        <div className="space-y-8 p-10 border border-white/10 bg-white/[0.02]">
          <div className="flex items-center gap-4 border-b border-white/10 pb-6">
            <Globe className="w-6 h-6 text-accent" />
            <div className="space-y-1">
              <h3 className="text-sm font-black uppercase tracking-widest">Network_Interface</h3>
              <p className="text-[9px] font-bold text-white/20 uppercase">Listening_State_Config</p>
            </div>
          </div>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-[9px] font-black text-white/30 uppercase tracking-[0.2em]" htmlFor="listening-ip">Listening_IP</label>
              <input 
                id="listening-ip"
                type="text" 
                defaultValue="0.0.0.0" 
                title="Listening IP"
                className="w-full bg-transparent border-b border-white/10 py-2 text-xs font-bold uppercase tracking-widest focus:outline-none focus:border-accent transition-colors"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[9px] font-black text-white/30 uppercase tracking-[0.2em]" htmlFor="listening-port">Listening_Port</label>
              <input 
                id="listening-port"
                type="text" 
                defaultValue="5000" 
                title="Listening Port"
                className="w-full bg-transparent border-b border-white/10 py-2 text-xs font-bold uppercase tracking-widest focus:outline-none focus:border-accent transition-colors"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[9px] font-black text-white/30 uppercase tracking-[0.2em]">Promiscuous_Mode</label>
              <div className="flex items-center gap-4 py-2">
                <div className="w-8 h-4 bg-accent/20 border border-accent/40 relative cursor-pointer" role="switch" aria-checked="true" title="Promiscuous Mode Toggle">
                  <div className="absolute left-0 top-0 bottom-0 w-4 bg-accent" />
                </div>
                <span className="text-[10px] font-black text-accent uppercase tracking-widest">ENABLED</span>
              </div>
            </div>
          </div>
        </div>

        {/* Security Policy */}
        <div className="space-y-8 p-10 border border-white/10 bg-white/[0.02]">
          <div className="flex items-center gap-4 border-b border-white/10 pb-6">
            <Shield className="w-6 h-6 text-accent" />
            <div className="space-y-1">
              <h3 className="text-sm font-black uppercase tracking-widest">Security_Policy</h3>
              <p className="text-[9px] font-bold text-white/20 uppercase">Enforcement_Behavior</p>
            </div>
          </div>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-[9px] font-black text-white/30 uppercase tracking-[0.2em]" htmlFor="default-action">Default_Action</label>
              <select 
                id="default-action"
                title="Default Action"
                className="w-full bg-black border-b border-white/10 py-2 text-xs font-bold uppercase tracking-widest focus:outline-none focus:border-accent transition-colors appearance-none cursor-pointer"
              >
                <option>BLOCK_UNKNOWN</option>
                <option>ALLOW_UNKNOWN</option>
                <option>QUARANTINE_UNKNOWN</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[9px] font-black text-white/30 uppercase tracking-[0.2em]" htmlFor="threshold-range">Auto_Quarantine_Threshold</label>
              <input 
                id="threshold-range"
                type="range" 
                title="Threshold Range"
                className="w-full h-1 bg-white/10 appearance-none cursor-pointer accent-accent"
              />
              <div className="flex justify-between text-[9px] font-bold text-white/20">
                <span>0%</span>
                <span>75% (CONFIDENCE)</span>
                <span>100%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-12">
        <button className="px-12 py-4 text-[10px] font-black uppercase tracking-[0.4em] bg-accent text-black hover:bg-white transition-colors flex items-center gap-3">
          Commit_Changes
          <Terminal className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
