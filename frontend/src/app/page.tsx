"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Sparkles, Map, Database, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useMutation } from "@tanstack/react-query";
import { locationApi } from "@/lib/api";
import { PredictionResults } from "@/features/prediction/components/PredictionResults";
import { toast } from "sonner";
import { useCallback, useEffect } from "react";
import { useDebounce } from "@/hooks/useDebounce";

export default function Home() {
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const debouncedQuery = useDebounce(query, 800);
  const [extractedKeywords, setExtractedKeywords] = useState<string[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);

  const predictMutation = useMutation({
    mutationFn: async (text: string) => {
      // First, try to resolve if it's a URL
      let tweetText = text;
      if (text.startsWith("http")) {
        const resolveRes = await locationApi.resolveTweetUrl(text);
        if (resolveRes.success && resolveRes.tweet_text) {
          tweetText = resolveRes.tweet_text;
          toast.success("URL resolved successfully");
        } else if (!resolveRes.success) {
          throw new Error(resolveRes.error || "Failed to resolve URL");
        }
      }
      
      const res = await locationApi.predictLocation(tweetText);
      if (!res.success) {
        throw new Error(res.error || "Failed to predict location");
      }
      return res;
    },
    onError: (error: Error) => {
      toast.error("Prediction Error", {
        description: error.message || "An unexpected error occurred."
      });
    },
    onSuccess: () => {
      toast.success("Prediction complete!");
    }
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      toast.warning("Please enter a tweet URL or text");
      return;
    }
    predictMutation.mutate(query);
  };

  // Debounced Keyword Extraction
  useEffect(() => {
    const extract = async () => {
      if (!debouncedQuery.trim() || debouncedQuery.startsWith("http")) {
        setExtractedKeywords([]);
        return;
      }
      try {
        setIsExtracting(true);
        const res = await locationApi.extractKeywords(debouncedQuery);
        if (res.success && res.keywords) {
          setExtractedKeywords(res.keywords);
        }
      } catch (err) {
        console.error("Keyword extraction failed", err);
      } finally {
        setIsExtracting(false);
      }
    };
    extract();
  }, [debouncedQuery]);

  return (
    <div className="flex min-h-screen w-full bg-background relative selection:bg-primary/30">
      <div className="aurora-bg">
        <div className="aurora-blob bg-primary/20 w-[600px] h-[600px] top-[-10%] left-[-10%] animation-delay-2000"></div>
        <div className="aurora-blob bg-accent/20 w-[500px] h-[500px] bottom-[-10%] right-[-10%] animation-delay-4000"></div>
        <div className="aurora-blob bg-blue-500/10 w-[400px] h-[400px] top-[40%] left-[60%]"></div>
      </div>
      <Sidebar />
      <main className="flex-1 flex flex-col relative z-10 overflow-hidden">
        
        <Navbar />
        
        <div className="flex-1 overflow-y-auto p-6 md:p-12 lg:p-24 flex flex-col items-center justify-center relative z-10">
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-3xl flex flex-col items-center text-center space-y-8"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-muted-foreground mb-4">
              <Sparkles className="w-4 h-4 text-primary" />
              <span>KDE AI Model V2.0 Online</span>
            </div>
            
            <h1 className="text-4xl md:text-6xl font-display font-bold tracking-tight text-foreground leading-tight">
              Where is this <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent animate-pulse">happening?</span>
            </h1>
            
            <p className="text-lg text-muted-foreground max-w-xl">
              Paste a tweet URL, text, or coordinates. Our AI will analyze semantics, extract geographic markers, and predict the exact city.
            </p>

            <form onSubmit={handleSearch} className="w-full relative mt-8">
              <div className={`relative flex items-center transition-all duration-500 ${isFocused ? 'scale-[1.02]' : 'scale-100'}`}>
                {/* Animated gradient border when focused */}
                <div className={`absolute -inset-0.5 bg-gradient-to-r from-primary via-accent to-primary rounded-2xl blur opacity-75 transition-opacity duration-500 ${isFocused ? 'opacity-100 animate-glow' : 'opacity-0'}`}></div>
                <div className="relative w-full flex items-center bg-background/80 backdrop-blur-xl border border-white/10 rounded-2xl p-2 shadow-2xl">
                  <div className="pl-4 pr-2 text-muted-foreground">
                    <Search className="w-5 h-5" />
                  </div>
                  <Input
                    type="text"
                    placeholder="Enter tweet URL or description..."
                    className="flex-1 bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-lg h-14 shadow-none"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                  />
                  <Button 
                    type="submit" 
                    size="icon" 
                    disabled={predictMutation.isPending}
                    className="h-12 w-12 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground transition-transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
                  >
                    {predictMutation.isPending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <ArrowRight className="w-5 h-5" />
                    )}
                  </Button>
                </div>
              </div>
            </form>

            {/* Extracted Keywords Preview */}
            <AnimatePresence>
              {extractedKeywords.length > 0 && !predictMutation.data && !predictMutation.isPending && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="w-full flex flex-wrap gap-2 justify-center mt-4"
                >
                  <span className="text-xs text-muted-foreground w-full mb-1">Detected entities:</span>
                  {extractedKeywords.map((kw, i) => (
                    <motion.span 
                      key={i}
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: i * 0.05 }}
                      className="px-3 py-1 text-xs font-medium bg-primary/10 border border-primary/20 rounded-full text-primary"
                    >
                      {kw}
                    </motion.span>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>

            <PredictionResults  
              isLoading={predictMutation.isPending} 
              prediction={predictMutation.data?.success ? predictMutation.data : null} 
            />

            {/* Quick Actions (Hide when searching) */}
            {!predictMutation.data && !predictMutation.isPending && (
              <motion.div 
                initial={{ opacity: 0 }} 
                animate={{ opacity: 1 }} 
                transition={{ delay: 0.5, duration: 0.8 }}
                className="flex flex-wrap items-center justify-center gap-4 mt-12 w-full"
              >
                <Button variant="outline" className="gap-2 rounded-full px-6 bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20 transition-all shadow-[0_0_15px_rgba(0,0,0,0.1)] hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]">
                  <Map className="w-4 h-4 text-primary" /> Browse Map
                </Button>
                <Button variant="outline" className="gap-2 rounded-full px-6 bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20 transition-all shadow-[0_0_15px_rgba(0,0,0,0.1)] hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]">
                  <Database className="w-4 h-4 text-accent" /> View Top 500 Cities
                </Button>
              </motion.div>
            )}
            
          </motion.div>
        </div>
      </main>
    </div>
  );
}
