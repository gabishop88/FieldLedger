import { AppShell, Paper } from "@mantine/core";

import AppHeader from "../components/header";
import SyncTreeSidebar from "../components/sidebar";
import LoginModal from "../components/login_modal";

import { useAuth } from "../hooks/use_auth";
import { useJDAuth } from "../hooks/use_jd_auth";
import { useSyncTree } from "../hooks/use_sync_tree";

import { useState } from "react";
import LogViewer from "../components/log_viewer";
import { type SyncTreeNode } from "../api/jd";
import FieldDetailsPanel from "../components/details_panel";

export default function Dashboard() {
    const { user, loading, logout, deleteAccount } = useAuth();
    const jdAuth = useJDAuth(!!user);
    const tree = useSyncTree(jdAuth.data?.authorized ?? false)

    const [loginOpened, setLoginOpened] = useState(false);
    const [selectedField, setSelectedField] = useState<SyncTreeNode | null>(null);
    const [selectedOp, setSelectedOp] = useState<SyncTreeNode | null>(null);

    function selectField(field: SyncTreeNode | null) {
        setSelectedField(field);
        setSelectedOp(null);
    }

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
                    gridTemplateColumns: "18vw 1fr",
                    gap: "1rem",
                    height: "70vh",
                }}
                >
                    <Paper withBorder style={{ overflow: "auto" }}>
                        <SyncTreeSidebar
                            loggedIn={!!user}
                            jdAuth={jdAuth.data ?? null}
                            trees={tree.data ?? []}
                            selectedField={selectedField}
                            onSelectField={selectField}
                        />
                    </Paper>

                    <Paper withBorder p="md" mih={0}>
                        <FieldDetailsPanel 
                            field={selectedField}
                            selectedOperation={selectedOp}
                            onSelectOperation={setSelectedOp}
                        />
                    </Paper>
                </div>

                <Paper withBorder p="md" mt="md" h="20vh">
                    <LogViewer />
                </Paper>
            </AppShell.Main>

            <LoginModal opened={loginOpened} onClose={() => setLoginOpened(false)} />
        </AppShell>
    );
}
