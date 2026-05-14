import axios from "axios";

// Configure base API using Next.js rewrites (see next.config.ts)
// The requests to /api/ will be proxied to http://127.0.0.1:8000/api/
export const apiClient = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export const locationApi = {
  predictLocation: async (tweet: string, cityBias?: string) => {
    const { data } = await apiClient.post("/predict/", { tweet, cityBias });
    return data;
  },
  
  predictBatch: async (tweets: string[], cityBias?: string) => {
    const { data } = await apiClient.post("/predict-batch/", { tweets, cityBias });
    return data;
  },

  searchCities: async (query: string) => {
    const { data } = await apiClient.get(`/city-search/?q=${encodeURIComponent(query)}`);
    return data;
  },

  getWorldCities: async () => {
    const { data } = await apiClient.get("/world-cities/");
    return data;
  },

  resolveTweetUrl: async (tweetUrl: string) => {
    const { data } = await apiClient.post("/resolve-tweet/", { tweetUrl });
    return data;
  },

  extractKeywords: async (text: string) => {
    const { data } = await apiClient.post("/extract-keywords/", { text });
    return data;
  }
};
