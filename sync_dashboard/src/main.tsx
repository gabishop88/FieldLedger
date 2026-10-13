import { useState, StrictMode, type ReactNode } from "react";
import ReactDOM from "react-dom/client";

import { createTheme, MantineProvider } from "@mantine/core";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Notifications } from "@mantine/notifications";

import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import "leaflet/dist/leaflet.css";

import App from "./App";
import AuthProvider from "./providers/auth_provider";

function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const theme = createTheme({ primaryColor: "green" });

  return <MantineProvider theme={theme} defaultColorScheme="auto">
    <Notifications />

    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        {children}
      </AuthProvider>
    </QueryClientProvider>
  </MantineProvider>
}


ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </StrictMode>
);
