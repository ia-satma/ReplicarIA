import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@/index.css";
import App from "@/App";

// Configure React Query with caching defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 seconds before data is considered stale
      gcTime: 300000, // 5 minutes cache time (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false, // Prevent refetch on tab focus
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
// Build: 1769731717
