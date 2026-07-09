import React from "react";
import ReactDOM from "react-dom/client";

import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";

import "leaflet/dist/leaflet.css";

import { createTheme, MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";

import App from "./App";
import QueryProvider from "./providers/query_provider";
import AuthProvider from "./providers/auth_provider";

const theme = createTheme({ primaryColor: "green" });

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <MantineProvider theme={theme} defaultColorScheme="dark">
            <Notifications />
            
            <QueryProvider>
                <AuthProvider>
                    <App />
                </AuthProvider>
            </QueryProvider>
        </MantineProvider>
    </React.StrictMode>,
);
