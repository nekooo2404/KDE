import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Search, MapPin, BarChart3, Settings, Cpu } from "lucide-react";

export function Sidebar() {
  return (
    <aside className="w-64 flex-shrink-0 hidden md:flex flex-col border-r border-white/10 bg-background/40 backdrop-blur-2xl h-screen sticky top-0 z-40 relative">
      <div className="absolute inset-y-0 right-0 w-[1px] bg-gradient-to-b from-transparent via-primary/30 to-transparent"></div>
      <div className="p-6 flex items-center gap-3 border-b border-white/5">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-[0_0_20px_rgba(var(--primary),0.3)]">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <span className="font-display font-bold text-2xl tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
          KDE AI
        </span>
      </div>
      
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        <Link href="/">
          <Button variant="secondary" className="w-full justify-start gap-3 rounded-xl h-12 bg-white/10 hover:bg-white/15 border border-white/10 transition-all font-medium text-white shadow-[0_0_15px_rgba(255,255,255,0.05)] group">
            <Search className="w-4 h-4 text-primary group-hover:animate-pulse" />
            Discover
          </Button>
        </Link>
        <Link href="/map">
          <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl h-12 text-muted-foreground hover:text-white hover:bg-white/5 transition-all group">
            <MapPin className="w-4 h-4 group-hover:text-accent transition-colors" />
            Global Map
          </Button>
        </Link>
        <Link href="/analytics">
          <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl h-12 text-muted-foreground hover:text-white hover:bg-white/5 transition-all group">
            <BarChart3 className="w-4 h-4 group-hover:text-primary transition-colors" />
            Analytics
          </Button>
        </Link>
      </nav>

      <div className="p-4 border-t border-white/5">
        <Link href="/settings">
          <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl h-12 text-muted-foreground hover:text-white hover:bg-white/5 transition-all group">
            <Settings className="w-4 h-4 group-hover:rotate-90 transition-transform duration-500" />
            Settings
          </Button>
        </Link>
      </div>
    </aside>
  );
}
