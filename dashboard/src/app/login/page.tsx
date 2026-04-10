"use client";

import { Shield, Lock, User, Eye, EyeOff, ChevronRight, Loader2 } from "lucide-react";
import { useState, useActionState } from "react";
import { authenticate } from "@/app/actions/auth-actions";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, action, isPending] = useActionState(
    authenticate,
    undefined,
  );

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-black font-mono selection:bg-accent selection:text-black relative overflow-hidden">
      <div className="scanline" />
      
      {/* Background Info (Minimal) */}
      <div className="absolute top-10 right-10 text-[9px] font-black uppercase tracking-[0.4em] text-white/5 text-right pointer-events-none select-none">
        Sentinel_NAC // v1.0.8<br />
        System_State: Listening<br />
        Encryption: AES-256-GCM
      </div>

      <div className="w-full max-w-sm relative z-10">
        <div className="border border-white/10 bg-black p-10 space-y-12 shadow-2xl">
          {/* Header */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 flex items-center justify-center border border-white/20">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <h1 className="text-sm font-black tracking-tighter uppercase">Sentinel-NAC</h1>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-black uppercase tracking-[0.4em] text-accent">Access_Request</p>
              <p className="text-[9px] font-bold text-white/20 uppercase tracking-widest">Operator_Validation_Required</p>
            </div>
          </div>

          {/* Form */}
          <form action={action} className="space-y-10">
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em] flex items-center gap-2">
                  <User className="w-3 h-3" />
                  Operator_ID
                </label>
                <input
                  name="username"
                  type="text"
                  placeholder="ID_NULL"
                  className="w-full bg-transparent border-b border-white/10 py-2 text-xs font-bold uppercase tracking-widest focus:outline-none focus:border-accent transition-colors placeholder:text-white/5"
                  required
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em] flex items-center gap-2">
                    <Lock className="w-3 h-3" />
                    Security_Cipher
                  </label>
                  <button 
                    type="button" 
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-[9px] font-bold text-white/10 hover:text-white transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
                <input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className="w-full bg-transparent border-b border-white/10 py-2 text-xs font-bold uppercase tracking-widest focus:outline-none focus:border-accent transition-colors placeholder:text-white/5"
                  required
                />
              </div>
            </div>

            {errorMessage && (
              <div className="text-[10px] font-black uppercase text-rose-500 tracking-widest flex items-center gap-2 border border-rose-500/20 bg-rose-500/5 p-3">
                <div className="w-1 h-1 bg-rose-500 rounded-full animate-pulse" />
                {errorMessage}
              </div>
            )}

            <button
              type="submit"
              disabled={isPending}
              className="w-full py-4 text-[10px] font-black uppercase tracking-[0.4em] border border-white/20 hover:border-accent hover:text-accent transition-all flex items-center justify-center gap-3 group relative overflow-hidden"
            >
              {isPending ? (
                <Loader2 className="w-4 h-4 text-accent animate-spin" />
              ) : (
                <>
                  Connect_Session <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Footer Info */}
          <div className="pt-8 border-t border-white/5 flex items-center justify-between">
            <div className="flex flex-col gap-1">
              <span className="text-[8px] font-black text-white/10 uppercase tracking-widest">Server_Status</span>
              <div className="flex items-center gap-2">
                <div className="w-1 h-1 bg-accent animate-pulse" />
                <span className="text-[9px] font-black text-accent uppercase tracking-widest">Active_Link</span>
              </div>
            </div>
            <div className="text-right flex flex-col gap-1">
              <span className="text-[8px] font-black text-white/10 uppercase tracking-widest">Recovery</span>
              <button className="text-[9px] font-black text-white/20 hover:text-white/40 uppercase tracking-widest transition-colors">Access_Reset</button>
            </div>
          </div>
        </div>
        
        <p className="mt-12 text-center text-[9px] text-white/10 font-black uppercase tracking-[0.5em] leading-relaxed select-none">
          SGP SECURE LABS // ACCESS_811_BETA<br />
          © 2026 PROPRIETARY_SYSTEM
        </p>
      </div>
    </div>
  );
}
