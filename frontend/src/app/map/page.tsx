"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { WorldMap } from "@/features/map/components/WorldMap";

export default function MapPage() {
  return (
    <div className="flex min-h-screen w-full bg-[#0a0a0a]">
      <Sidebar />
      <main className="flex-1 flex flex-col relative h-screen">
        <Navbar />
        
        {/* Full bleed map container */}
        <div className="flex-1 relative w-full h-full bg-[#050505]">
          <WorldMap />
          
          <div className="absolute bottom-8 left-8 z-10 glass-card p-4 pointer-events-none">
            <h3 className="text-white font-semibold">Global Distribution</h3>
            <p className="text-sm text-muted-foreground mt-1">Live visualization of top 200,000 cities</p>
            <div className="flex items-center gap-2 mt-3">
              <div className="w-3 h-3 rounded-full bg-primary/80"></div>
              <span className="text-xs text-white/70">City Node</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
