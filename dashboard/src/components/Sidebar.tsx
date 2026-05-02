"use client";

import { useState, useEffect } from "react"; // Added useEffect for hydration fix
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSession, signOut } from "next-auth/react";

import {
  Shield,
  LayoutDashboard,
  Network,
  Bell,
  FileBarChart,
  Settings,
  LogOut,
  Terminal,
} from "lucide-react";

const navItems = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Nodes", href: "/devices", icon: Network },
  { name: "Alerts", href: "/alerts", icon: Bell },
  { name: "Logs", href: "/reports", icon: FileBarChart },
  { name: "System", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  // DEMO MODE: Force admin role
  const role = "superadmin";
  const name = "ADMIN";
  const status = "ACTIVE";
  const pathname = usePathname();
  const { data: session } = useSession();
  const [mounted, setMounted] = useState(false);

  // Fix hydration mismatch by waiting for client-side mount
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <aside className="w-64 bg-black border-r border-white/10 flex flex-col h-screen sticky top-0 font-mono">
      {/* Brand Header */}
      <div className="p-8 border-b border-white/5">
        <div className="flex items-center gap-3 group">
          <div className="w-8 h-8 flex items-center justify-center border border-white/20 group-hover:border-accent transition-colors">
            <Shield className="w-4 h-4 text-white group-hover:text-accent transition-colors" />
          </div>
          <div className="space-y-0.5">
            <h1 className="text-xs font-black tracking-tighter uppercase">
              Sentinel-NAC
            </h1>
            <p className="text-[9px] text-white/30 uppercase font-bold tracking-widest">
              Core Engine v1.0
            </p>
          </div>
        </div>
      </div>

      {/* Primary Navigation */}
      <nav className="flex-1 py-8 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-4 px-8 py-2.5 text-[11px] font-bold uppercase tracking-widest transition-all relative group",
                isActive
                  ? "text-accent bg-accent/5"
                  : "text-white/40 hover:text-white hover:bg-white/5"
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-accent shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
              )}
              <item.icon
                className={cn(
                  "w-4 h-4 transition-colors",
                  isActive ? "text-accent" : "text-white/20 group-hover:text-white"
                )}
              />
              {item.name}
              {item.name === "Alerts" && (
                <span className="ml-auto text-[10px] text-accent/60">[03]</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Terminal-like Status Footer */}
      <div className="p-8 mt-auto space-y-6">
        <div className="space-y-3">
          <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest text-white/20">
            <span>Operator</span>
            <span className="text-white/40 font-mono flex flex-col items-end">
              <span>{mounted ? name : '...'}</span>
              <span className="text-[7px] text-accent/40">{mounted ? role.toUpperCase() : 'INITIALIZING'}</span>
            </span>
          </div>
          <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest text-white/20">
            <span>Uptime</span>
            <span className="text-white/40 font-mono">00:42:12</span>
          </div>
          <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest text-white/20">
            <span>Auth Status</span>
            <span className="text-accent/60 font-mono flex items-center gap-1">
              <div className="w-1 h-1 bg-accent rounded-full animate-pulse" />
              {mounted ? status : 'READY'}
            </span>
          </div>
        </div>

        <a 
          href="/api/auth/signout"
          className="w-full py-2.5 text-[10px] font-black uppercase tracking-[0.2em] border border-white/10 hover:border-white hover:bg-white hover:text-black transition-all flex items-center justify-center gap-2 group"
        >
          <LogOut className="w-3.5 h-3.5 group-hover:-translate-x-1 transition-transform" />
          Disconnect_Session
        </a>

        <p className="text-[9px] text-center text-white/10 font-bold uppercase tracking-widest">
          SGP SECURE LABS // ACCESS 811
        </p>
      </div>
    </aside>
  );
}
