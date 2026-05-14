"use client";

import { useState } from "react";
import { Bell, Command, UserCircle, Menu, X, Search, MapPin, BarChart3, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

export function Navbar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <header className="h-16 border-b border-white/10 bg-background/40 backdrop-blur-2xl flex items-center justify-between px-6 sticky top-0 z-40 relative">
      <div className="absolute inset-x-0 bottom-0 h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent"></div>
      <div className="flex items-center gap-4 flex-1">
        <div className="md:hidden">
          <Button variant="ghost" size="icon" onClick={() => setIsMobileMenuOpen(true)}>
            <Menu className="w-6 h-6 text-white" />
          </Button>
        </div>
        <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground bg-white/5 px-4 py-1.5 rounded-full border border-white/10 shadow-sm backdrop-blur-md transition-colors hover:bg-white/10 cursor-pointer">
          <Command className="w-3.5 h-3.5" />
          <span>Press <kbd className="font-display font-medium text-xs bg-black/40 text-white rounded px-1.5 py-0.5 shadow-sm border border-white/10">⌘K</kbd> to command</span>
        </div>
      </div>
      
      <div className="flex items-center gap-3 relative z-10">
        <Button variant="ghost" size="icon" className="rounded-full relative hover:bg-white/10 transition-colors">
          <Bell className="w-5 h-5 text-muted-foreground hover:text-white transition-colors" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-accent rounded-full animate-pulse shadow-[0_0_8px_rgba(var(--accent),0.8)]"></span>
        </Button>
        <div className="hidden md:block w-px h-6 bg-white/10 mx-2"></div>
        <Button variant="ghost" className="gap-2 rounded-full pl-2 pr-4 bg-white/5 border border-white/10 hover:bg-white/15 transition-all shadow-sm hidden md:flex">
          <UserCircle className="w-6 h-6 text-primary" />
          <span className="text-sm font-display font-medium text-white/90">Admin</span>
        </Button>
      </div>

      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div 
            initial={{ opacity: 0, x: -300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className="fixed inset-0 z-50 bg-background/95 backdrop-blur-2xl flex flex-col md:hidden border-r border-white/10 w-3/4 max-w-sm"
          >
            <div className="p-4 flex justify-between items-center border-b border-white/10">
              <span className="font-display font-bold text-xl tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                KDE AI
              </span>
              <Button variant="ghost" size="icon" onClick={() => setIsMobileMenuOpen(false)}>
                <X className="w-6 h-6" />
              </Button>
            </div>
            <nav className="flex-1 p-4 space-y-4">
              <Link href="/" onClick={() => setIsMobileMenuOpen(false)}>
                <Button variant="secondary" className="w-full justify-start gap-3 rounded-xl h-12 bg-white/10 text-white mb-2">
                  <Search className="w-5 h-5 text-primary" /> Discover
                </Button>
              </Link>
              <Link href="/map" onClick={() => setIsMobileMenuOpen(false)}>
                <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl h-12 text-muted-foreground hover:text-white mb-2">
                  <MapPin className="w-5 h-5" /> Global Map
                </Button>
              </Link>
              <Link href="/analytics" onClick={() => setIsMobileMenuOpen(false)}>
                <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl h-12 text-muted-foreground hover:text-white mb-2">
                  <BarChart3 className="w-5 h-5" /> Analytics
                </Button>
              </Link>
              <Link href="/settings" onClick={() => setIsMobileMenuOpen(false)}>
                <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl h-12 text-muted-foreground hover:text-white mt-8 border-t border-white/10">
                  <Settings className="w-5 h-5" /> Settings
                </Button>
              </Link>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
      
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 md:hidden" 
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </header>
  );
}
