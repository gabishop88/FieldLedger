import { useMemo, useRef, useState } from "react";
import { AppShell, Button, Divider, Group, Paper, Splitter, Stack, ThemeIcon, Title, useMantineColorScheme } from "@mantine/core";
import { type UseSplitterReturnValue } from "@mantine/hooks";

import AccountMenu from "../components/auth/account_menu";
import JDAuthButtons from "../components/auth/jd_auth_buttons";
import LoginModal from "../components/auth/login_modal";
import FieldDetailsPanel from "../components/sync/field_details";
import { isActive } from "../components/sync/status_info";
import SyncTree from "../components/sync/sync_tree";
import { FieldNotSelectedCard, NotConnectedCard, NotLoggedInCard } from "../components/instruction_cards";
import LogViewer from "../components/log_viewer";

import { useAuth } from "../hooks/use_auth";
import { useJDAuth } from "../hooks/use_jd_auth";
import { useSyncTree } from "../hooks/use_sync_tree";
import { IconMoonFilled, IconSunFilled } from "@tabler/icons-react";
import type { AnySyncLink, SyncLink } from "../types/fl";

export default function Dashboard() {
  const { toggleColorScheme } = useMantineColorScheme();
  const { user, loading, logout, deleteAccount } = useAuth();
  const jdAuth = useJDAuth(!!user);
  const tree = useSyncTree(jdAuth.data?.authorized ?? false)

  const splitterRef = useRef<UseSplitterReturnValue>(null);

  const [loginOpened, setLoginOpened] = useState(false);
  const [selectedFieldUri, setSelectedFieldUri] = useState<string | null>(null);
  const [selectedOpUri, setSelectedOpUri] = useState<string | null>(null);
  const activeSelectedFieldFilter = (node: AnySyncLink | null): SyncLink<"field"> | null => {
    if (!node) return null;
    if (node.table_name === "field" && node.uri === selectedFieldUri && isActive(node)) return node;
    return node.children.find(activeSelectedFieldFilter) as SyncLink<"field"> | null;
  }
  const selectedField = useMemo(() => {
    const field = !selectedFieldUri ? null : tree.data?.flatMap(org => org.children).find(activeSelectedFieldFilter) as SyncLink<"field"> | null;
    if (selectedFieldUri && !field) setSelectedFieldUri(null);
    return field;
  }, [selectedFieldUri, tree]);

  const selectedOp = useMemo(() => 
    selectedField ? selectedField?.children
      .filter(c => c.table_name === "field_op")
      .find(op => op.uri === selectedOpUri)
    ?? null : null,
    [selectedOpUri, selectedField]
  );

  return <AppShell header={{ height: "7vh" }} padding="md">
    <LoginModal opened={loginOpened} onClose={() => setLoginOpened(false)} />
    
    {/* Page Header: Title, Account Management, Color Scheme Toggle */}
    <AppShell.Header>
      <Group w="100%" h="100%" justify="space-between" align="center" px="lg">
        <Title>FieldLedger Sync</Title>
        <Group h="100%">
          <AccountMenu
            user={user}
            loading={loading}
            onLogin={() => setLoginOpened(true)}
            onLogout={logout}
            onDeleteAccount={deleteAccount}
          />
          <Button
            color="cyan"
            size="compact-lg"
            variant="light"
            radius="lg"
            leftSection={<ThemeIcon lightHidden radius="xl" color="gray"><IconMoonFilled /></ThemeIcon>}
            rightSection={<ThemeIcon darkHidden radius="xl" color="yellow.6" variant="subtle"><IconSunFilled /></ThemeIcon>}
            onClick={toggleColorScheme}
          />
        </Group>
      </Group>
    </AppShell.Header>

    {/* Page Body: Side Panel for Org/Farm/Field tree, main panel for Field/Op Details, bottom panel for backend logs. */}
    <AppShell.Main bg="var(--mantine-color-default-hover)">
      <Splitter splitterRef={splitterRef} orientation="vertical" h="90vh" lineSize={6} handleColor="primary">
        <Splitter.Pane defaultSize={75} min={15}>
          <Group align="stretch" h="100%" mih={0} gap="xs">
            <Paper withBorder h="100%" miw={320} flex={1}>
              <Stack h="100%" gap={0}>
                <JDAuthButtons loggedIn={!!user} jdAuth={jdAuth.data ?? null} />
                <Divider />
                <SyncTree trees={tree.data ?? []} selectedField={selectedField} onSelectField={setSelectedFieldUri} />
              </Stack>
            </Paper>

            <Paper withBorder p="md" h="100%" flex={4}>
              {
                !user ? <NotLoggedInCard /> :
                !jdAuth.data?.authorized ? <NotConnectedCard /> :
                !selectedField ? <FieldNotSelectedCard /> :
                <FieldDetailsPanel
                  field={selectedField}
                  selectedOp={selectedOp}
                  onSelectOp={setSelectedOpUri}
                />
              }
            </Paper>
          </Group>
        </Splitter.Pane>

        <Splitter.Pane defaultSize={25} min={5} collapsible>
          <Paper withBorder p="md" h="100%" mih={0}>
            <LogViewer
              toggleCollapse={() => splitterRef.current?.toggleCollapse(1)}
            />
          </Paper>
        </Splitter.Pane>
      </Splitter>
    </AppShell.Main>
  </AppShell>;
}
