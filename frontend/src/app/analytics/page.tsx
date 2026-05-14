"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

// Lazy load Recharts to reduce main bundle size
const DashboardCharts = dynamic(
  () => import("@/features/analytics/components/DashboardCharts").then((mod) => mod.DashboardCharts),
  { 
    ssr: false, 
    loading: () => (
      <div className="w-full h-[600px] flex items-center justify-center glass-card">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
      </div>
    )
  }
);

export default function AnalyticsPage() {
  return (
    <div className="flex min-h-screen w-full bg-background relative selection:bg-primary/30">
      <div className="aurora-bg">
        <div className="aurora-blob bg-purple-500/20 w-[500px] h-[500px] top-0 right-0 animation-delay-2000"></div>
        <div className="aurora-blob bg-primary/10 w-[600px] h-[600px] bottom-[-20%] left-[-10%]"></div>
      </div>
      <Sidebar />
      <main className="flex-1 flex flex-col relative overflow-hidden h-screen z-10">
        
        <Navbar />
        
        <div className="flex-1 overflow-y-auto p-6 md:p-10 z-10">
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-6"
          >
            <div>
              <h1 className="text-3xl md:text-4xl font-display font-bold tracking-tight text-white mb-2">Analytics Overview</h1>
              <p className="text-muted-foreground">Monitor AI model performance, prediction confidence, and geographic distribution.</p>
            </div>
            
            <DashboardCharts />
          </motion.div>
        </div>
      </main>
    </div>
  );
}
