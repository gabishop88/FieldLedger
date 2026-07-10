import { useMemo, useState } from "react";
import { ActionIcon, AppShell, Box, Center, Group, Paper, Stack, Title, useMantineColorScheme } from "@mantine/core";

import SyncExplorerPanel from "../components/sync/sync_explorer";
import LoginModal from "../components/auth/login_modal";

import { useAuth } from "../hooks/use_auth";
import { useJDAuth } from "../hooks/use_jd_auth";
import { useSyncTree } from "../hooks/use_sync_tree";

import LogViewer from "../components/log_viewer";
import FieldDetailsPanel from "../components/sync/field_details";

import type { JDField, JDFieldOp } from "../types/jd";
import type { SyncLink } from "../types/fl";
import { IconMoonFilled, IconSunFilled } from "@tabler/icons-react";
import AccountMenu from "../components/auth/account_menu";

export default function Dashboard() {
    const { toggleColorScheme } = useMantineColorScheme();

    const { user, loading, logout, deleteAccount } = useAuth();
    const jdAuth = useJDAuth(!!user);
    const tree = useSyncTree(jdAuth.data?.authorized ?? false)

    const [loginOpened, setLoginOpened] = useState(false);
    const [selectedFieldUri, setSelectedFieldUri] = useState<string | null>(null);
    const [selectedOpUri, setSelectedOpUri] = useState<string | null>(null);

    const selectedField = useMemo(
        () => !selectedFieldUri ? null : (
            tree.data?.flatMap(org => org.children).flatMap(farm => farm.children)
                .find(field => field.uri === selectedFieldUri)
        ) as SyncLink<JDField> | null,
        [selectedFieldUri, tree]
    );
    const selectedOp = useMemo(
        () => !selectedField ? null : (
            selectedField?.children.find(op => op.uri === selectedOpUri)
        ) as SyncLink<JDFieldOp> | null,
        [selectedOpUri, selectedField]
    );

    function selectField(field: SyncLink<JDField> | null) {
        setSelectedFieldUri(field?.uri ?? null);
        setSelectedOpUri(null);
    }
    function selectOp(op: SyncLink<JDFieldOp> | null) {
        setSelectedOpUri(op?.uri ?? null);
    }

    return (
        <AppShell header={{ height: "8vh" }} padding="md">
            <LoginModal opened={loginOpened} onClose={() => setLoginOpened(false)} />

            <AppShell.Header>
                <Center h="100%" px="1vw">
                    <Group justify="space-between" w="100%" align="flex-end">
                        <Title>FieldLedger Sync</Title>

                        <Group>
                            <ActionIcon variant="default" size="xl" onClick={toggleColorScheme}>
                                <Box lightHidden><IconSunFilled /></Box>
                                <Box darkHidden><IconMoonFilled /></Box>
                            </ActionIcon>

                            <AccountMenu 
                                user={user}
                                loading={loading}
                                onLogin={() => setLoginOpened(true)}
                                onLogout={logout}
                                onDeleteAccount={deleteAccount}
                            />
                        </Group>
                    </Group>
                </Center>
            </AppShell.Header>

            <AppShell.Main>
                <Stack gap="1vh">
                    <Box
                        style={{
                            display: "grid",
                            gridTemplateColumns: "18vw 1fr",
                            gap: "0.75vw",
                            height: "65vh",
                        }}
                    >
                        <Paper withBorder p="md" mih={0}>
                                <SyncExplorerPanel
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
                                onSelectOperation={selectOp}
                                />
                        </Paper>
                    </Box>

                    <Paper withBorder p="md" h="22.5vh">
                        <LogViewer />
                    </Paper>
                </Stack>
            </AppShell.Main>
        </AppShell>
    );
}
