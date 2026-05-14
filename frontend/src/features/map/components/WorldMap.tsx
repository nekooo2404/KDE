import { useEffect, useState } from "react";
import { ComposableMap, Geographies, Geography, Marker, ZoomableGroup } from "react-simple-maps";
import { locationApi } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { X, Users, Maximize, MapPin, Sparkles, Building, Landmark, Utensils } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getInsightsForCountry } from "@/lib/countryData";

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

export function WorldMap() {
  const [cities, setCities] = useState<any[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<any>(null);
  const [countryDetails, setCountryDetails] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    locationApi.getWorldCities()
      .then(data => {
        const allCities = Array.isArray(data) ? data : (data?.points || []);
        setCities(allCities.slice(0, 8000));
      })
      .catch(console.error);
  }, []);

  const handleCountryClick = async (geo: any) => {
    const countryName = geo.properties.name;
    setSelectedCountry(countryName);
    setIsLoading(true);
    setCountryDetails(null);

    try {
      // Gọi API thực tế để lấy dân số, diện tích, cờ...
      const res = await fetch(`https://restcountries.com/v3.1/name/${countryName}?fullText=true`);
      const data = await res.json();
      
      if (data && data[0]) {
        const aiInsights = getInsightsForCountry(countryName);
        setCountryDetails({
          ...data[0],
          aiInsights
        });
      }
    } catch (err) {
      console.error("Failed to fetch country data");
      // Fallback nếu API lỗi
      setCountryDetails({
        name: { common: countryName },
        aiInsights: getInsightsForCountry(countryName)
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full h-full relative overflow-hidden">
      <div className="w-full h-full cursor-grab active:cursor-grabbing">
        <ComposableMap
          projectionConfig={{
            scale: 160,
            center: [0, 20]
          }}
          width={900}
          height={500}
          style={{ width: "100%", height: "100%" }}
        >
          <ZoomableGroup zoom={1} minZoom={1} maxZoom={8}>
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geo) => {
                  const isSelected = selectedCountry === geo.properties.name;
                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      onClick={() => handleCountryClick(geo)}
                      fill={isSelected ? "#8b5cf6" : "#1a1a24"}
                      stroke="#2d2d3d"
                      strokeWidth={0.5}
                      style={{
                        default: { outline: "none", transition: "all 250ms" },
                        hover: { fill: "#3b82f6", outline: "none", cursor: "pointer" },
                        pressed: { fill: "#8b5cf6", outline: "none" },
                      }}
                    />
                  );
                })
              }
            </Geographies>
            
            {cities.map((city, i) => (
              <Marker key={i} coordinates={[city.lon, city.lat]}>
                <circle r={0.8} fill="#ffffff" fillOpacity={0.4} />
              </Marker>
            ))}
          </ZoomableGroup>
        </ComposableMap>
      </div>

      {/* Side Panel hiển thị thông tin quốc gia */}
      <AnimatePresence>
        {selectedCountry && (
          <motion.div
            initial={{ x: "100%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "100%", opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="absolute top-0 right-0 w-full md:w-[450px] lg:w-[500px] h-full bg-background/85 backdrop-blur-3xl border-l border-white/10 shadow-2xl z-50 overflow-y-auto"
          >
            <div className="p-8">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-3xl font-bold text-white flex items-center gap-4">
                  {countryDetails?.flags?.svg && (
                    <img src={countryDetails.flags.svg} alt="flag" className="w-10 h-7 rounded shadow-sm object-cover" />
                  )}
                  {selectedCountry}
                </h2>
                <Button variant="ghost" size="icon" onClick={() => setSelectedCountry(null)} className="rounded-full w-10 h-10 hover:bg-white/10">
                  <X className="w-6 h-6" />
                </Button>
              </div>

              {isLoading ? (
                <div className="space-y-6">
                  <div className="h-28 bg-white/5 animate-pulse rounded-2xl"></div>
                  <div className="h-48 bg-white/5 animate-pulse rounded-2xl"></div>
                </div>
              ) : countryDetails ? (
                <div className="space-y-8">
                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-4 shadow-sm">
                      <div className="flex items-center gap-3 text-muted-foreground mb-2">
                        <Users className="w-5 h-5 text-blue-400" />
                        <span className="text-sm font-medium uppercase tracking-wider">Dân số</span>
                      </div>
                      <p className="text-lg font-bold text-white">
                        {countryDetails.population ? new Intl.NumberFormat().format(countryDetails.population) : "N/A"}
                      </p>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-4 shadow-sm">
                      <div className="flex items-center gap-3 text-muted-foreground mb-2">
                        <Maximize className="w-5 h-5 text-green-400" />
                        <span className="text-sm font-medium uppercase tracking-wider">Diện tích</span>
                      </div>
                      <p className="text-lg font-bold text-white">
                        {countryDetails.area ? `${new Intl.NumberFormat().format(countryDetails.area)} km²` : "N/A"}
                      </p>
                    </div>
                  </div>

                  {countryDetails.capital && (
                    <div className="flex items-center gap-4 bg-white/5 border border-white/10 rounded-2xl p-5 shadow-sm">
                      <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                        <MapPin className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground uppercase tracking-wider font-medium mb-1">Thủ đô</p>
                        <p className="text-xl font-bold text-white">{countryDetails.capital[0]}</p>
                      </div>
                    </div>
                  )}

                  {/* AI Insights Section */}
                  <div className="mt-10 space-y-6">
                    <div className="flex items-center gap-3">
                      <Sparkles className="w-6 h-6 text-purple-400" />
                      <h3 className="text-2xl font-bold text-white tracking-tight">AI Insights</h3>
                    </div>
                    
                    <div className="space-y-6">
                      <div className="bg-gradient-to-br from-purple-500/15 to-blue-500/15 border border-purple-500/30 rounded-2xl p-5 shadow-inner">
                        <p className="text-base text-white/95 leading-relaxed font-medium">
                          {countryDetails.aiInsights.culture}
                        </p>
                      </div>

                      <div className="space-y-4">
                        <h4 className="text-base font-semibold text-muted-foreground flex items-center gap-2 uppercase tracking-wide">
                          <Landmark className="w-5 h-5" /> Danh lam & Di tích
                        </h4>
                        <div className="flex flex-wrap gap-3">
                          {countryDetails.aiInsights.landmarks.map((item: string, idx: number) => (
                            <span key={idx} className="text-sm font-medium px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white shadow-sm hover:bg-white/20 transition-colors cursor-default">
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h4 className="text-base font-semibold text-muted-foreground flex items-center gap-2 uppercase tracking-wide">
                          <Utensils className="w-5 h-5" /> Đặc sản ẩm thực
                        </h4>
                        <div className="flex flex-wrap gap-3">
                          {countryDetails.aiInsights.specialties.map((item: string, idx: number) => (
                            <span key={idx} className="text-sm font-medium px-4 py-2 bg-orange-500/15 border border-orange-500/30 rounded-lg text-orange-200 shadow-sm hover:bg-orange-500/25 transition-colors cursor-default">
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                </div>
              ) : (
                <div className="text-center text-lg text-muted-foreground py-12">
                  Không tìm thấy dữ liệu chi tiết cho khu vực này.
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
