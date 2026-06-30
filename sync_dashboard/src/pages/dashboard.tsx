import { AppShell, Paper } from "@mantine/core";

import AppHeader from "../components/header";
import SyncTreeSidebar from "../components/sidebar";
import LoginModal from "../components/login_modal";

import { useAuth } from "../hooks/use_auth";
import { useJDAuth } from "../hooks/use_jd_auth";
import { useSyncTree } from "../hooks/use_sync_tree";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";

export default function Dashboard() {
    const { user, loading, logout, deleteAccount } = useAuth();
    const jdAuth = useJDAuth(!!user);
    const tree = useSyncTree(jdAuth.data?.authorized ?? false)

    const [loginOpened, setLoginOpened] = useState(false);

    const queryClient = useQueryClient();
    useEffect(() => {
        const handleFocus = () => queryClient.refetchQueries({ queryKey: ["jd"] });
        window.addEventListener("focus", handleFocus);

        const params = new URLSearchParams(window.location.search);
        const result = params.get("jd-connected");
        if (result) {
            handleFocus();
            notifications.show({
                color: result == "authorized" ? "green" : "red",
                title: `Connection ${result[0].toUpperCase()}${result.slice(1)}`,
                message: result == "authorized"
                    ? "John Deere authorization completed successfully."
                    : "Unable to connect to your John Deere account."
            });
            window.history.replaceState({}, "", window.location.pathname);
        }
        return () => window.removeEventListener("focus", handleFocus)
    }, [queryClient])

    return (
        <AppShell header={{ height: 80 }} padding="md">
            <AppHeader
                user={user}
                loading={loading}
                onLogin={() => setLoginOpened(true)}
                onLogout={logout}
                onDeleteAccount={deleteAccount}
            />
            <AppShell.Main>
                <div style={{
                    display: "grid",
                    gridTemplateColumns: "300px 1fr",
                    gap: "1rem",
                    height: "70vh",
                }}
                >
                    <Paper withBorder>
                        <SyncTreeSidebar
                            loggedIn={!!user}
                            jdAuth={jdAuth.data ?? null}
                            trees={tree.data ?? []}
                        />
                    </Paper>

                    <Paper withBorder p="md">
                        Detail Panel
                    </Paper>
                </div>

                <Paper withBorder p="md" mt="md" h={180}>
                    Worker Log
                </Paper>
            </AppShell.Main>

            <LoginModal opened={loginOpened} onClose={() => setLoginOpened(false)} />
        </AppShell>
    );
}
