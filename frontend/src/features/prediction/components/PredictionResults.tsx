import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MapPin, Target, Zap, Globe2 } from "lucide-react";
import { motion } from "framer-motion";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

interface PredictionResultsProps {
  prediction: {
    predicted_city: string;
    predicted_city_point?: { lat: number; lon: number; city: string; score?: number } | null;
    confidence: number;
    prediction_source: string;
    terms_found: number;
    terms: string[];
    top_cities: { city: string; score: number }[];
  } | null;
  isLoading?: boolean;
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

export function PredictionResults({ prediction, isLoading }: PredictionResultsProps) {
  if (isLoading) {
    return (
      <div className="w-full max-w-3xl mt-8 space-y-4">
        <div className="h-48 bg-white/5 animate-pulse rounded-2xl border border-white/10 backdrop-blur-md"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-24 bg-white/5 animate-pulse rounded-2xl border border-white/10 backdrop-blur-md"></div>
          <div className="h-24 bg-white/5 animate-pulse rounded-2xl border border-white/10 backdrop-blur-md"></div>
        </div>
      </div>
    );
  }

  if (!prediction) return null;

  const confidenceScore = prediction.confidence * 100;
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (confidenceScore / 100) * circumference;

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="w-full max-w-3xl mt-8 space-y-6 text-left"
    >
      <motion.div variants={itemVariants}>
        <Card className="glass-card overflow-hidden relative">
          <div className="absolute -top-32 -right-32 w-64 h-64 bg-primary/20 rounded-full blur-[100px]" />
          <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-accent/20 rounded-full blur-[100px]" />
          
          <CardHeader className="pb-2 border-b border-white/5 relative z-10">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-xl font-display">
                <MapPin className="w-5 h-5 text-primary" />
                Predicted Location
              </CardTitle>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/30 shadow-[0_0_15px_rgba(var(--primary),0.2)]">
                <Zap className="w-4 h-4 text-primary animate-pulse" />
                <span className="text-xs font-bold text-primary uppercase tracking-wider">
                  {prediction.prediction_source}
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6 relative z-10">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div>
                <h2 className="text-5xl md:text-6xl font-display font-bold tracking-tight bg-gradient-to-br from-white via-white/90 to-white/50 bg-clip-text text-transparent">
                  {prediction.predicted_city}
                </h2>
                <div className="flex items-center gap-2 mt-3 text-muted-foreground bg-white/5 w-fit px-3 py-1 rounded-md border border-white/10">
                  <Globe2 className="w-4 h-4 text-accent" />
                  <span className="text-sm">Primary Match</span>
                </div>
              </div>
              
              <div className="flex items-center gap-4 bg-black/20 p-4 rounded-2xl border border-white/5">
                <div className="relative w-20 h-20 flex items-center justify-center">
                  <svg className="transform -rotate-90 w-20 h-20">
                    <circle cx="40" cy="40" r={radius} stroke="currentColor" strokeWidth="6" fill="transparent" className="text-white/10" />
                    <motion.circle
                      initial={{ strokeDashoffset: circumference }}
                      animate={{ strokeDashoffset }}
                      transition={{ duration: 1.5, ease: "easeOut" }}
                      cx="40" cy="40" r={radius} stroke="currentColor" strokeWidth="6" fill="transparent"
                      strokeDasharray={circumference}
                      className="text-primary drop-shadow-[0_0_8px_rgba(var(--primary),0.5)]"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="font-display font-bold text-xl">{confidenceScore.toFixed(0)}%</span>
                  </div>
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-muted-foreground">Confidence</span>
                  <span className="text-xs text-white/50">Score</span>
                </div>
              </div>
            </div>

            {prediction.terms && prediction.terms.length > 0 && (
              <div className="mt-8 pt-6 border-t border-white/5">
                <h4 className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                  <Target className="w-4 h-4" /> Extracted Geographic Markers
                </h4>
                <motion.div 
                  variants={containerVariants}
                  className="flex flex-wrap gap-2"
                >
                  {prediction.terms.map((term, i) => (
                    <motion.span 
                      variants={itemVariants}
                      key={i} 
                      className="px-4 py-1.5 text-sm font-medium bg-gradient-to-r from-white/10 to-white/5 border border-white/10 rounded-xl text-white/90 shadow-sm"
                    >
                      {term}
                    </motion.span>
                  ))}
                </motion.div>
              </div>
            )}

            {/* Interactive Map */}
            {prediction.predicted_city_point && prediction.predicted_city_point.lat && prediction.predicted_city_point.lon && (
              <div className="mt-8 pt-6 border-t border-white/5 relative">
                <h4 className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                  <MapPin className="w-4 h-4" /> Global View
                </h4>
                <div className="w-full h-[250px] bg-black/20 rounded-xl border border-white/5 overflow-hidden">
                  <ComposableMap
                    projection="geoMercator"
                    projectionConfig={{ scale: 100 }}
                    className="w-full h-full"
                  >
                    <Geographies geography={geoUrl}>
                      {({ geographies }) =>
                        geographies.map((geo) => (
                          <Geography
                            key={geo.rsmKey}
                            geography={geo}
                            fill="rgba(255,255,255,0.05)"
                            stroke="rgba(255,255,255,0.1)"
                            strokeWidth={0.5}
                            style={{
                              default: { outline: "none" },
                              hover: { fill: "rgba(255,255,255,0.1)", outline: "none" },
                              pressed: { outline: "none" },
                            }}
                          />
                        ))
                      }
                    </Geographies>
                    <Marker coordinates={[prediction.predicted_city_point.lon, prediction.predicted_city_point.lat]}>
                      <motion.g
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 200, damping: 10, delay: 0.5 }}
                      >
                        <circle r={6} fill="hsl(var(--primary))" />
                        <circle r={18} fill="hsl(var(--primary))" opacity={0.3} className="animate-ping" />
                      </motion.g>
                    </Marker>
                  </ComposableMap>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {prediction.top_cities?.slice(1, 5).map((city, idx) => (
          <motion.div 
            whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.08)" }}
            key={idx} 
            className="glass-card p-4 flex items-center justify-between group transition-all border border-white/5 hover:border-primary/30 cursor-default"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-white/10 to-white/5 flex items-center justify-center text-sm font-bold text-muted-foreground group-hover:text-primary transition-colors border border-white/10">
                #{idx + 2}
              </div>
              <span className="font-display font-medium text-lg text-white/90">{city.city}</span>
            </div>
            <div className="flex flex-col items-end">
              <span className="font-mono text-sm font-semibold text-primary/90">{(city.score * 100).toFixed(1)}%</span>
              <div className="w-16 h-1.5 bg-white/10 rounded-full mt-1 overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${city.score * 100}%` }}
                  transition={{ duration: 1, delay: 0.5 }}
                  className="h-full bg-primary"
                />
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </motion.div>
  );
}
