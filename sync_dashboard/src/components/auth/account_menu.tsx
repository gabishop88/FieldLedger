import { Button, Menu, Stack, Text, ThemeIcon } from "@mantine/core";

import { useState } from "react";
import ConfirmationModal from "./confirm_modal";
import type { User } from "../../types/fl";
import { IconLogout, IconTrash, IconUser, IconUserBolt } from "@tabler/icons-react";
import { useAuth } from "../../hooks/use_auth";
import LoginModal from "./login_modal";

interface Props {
  user: User | null;
  loading: boolean;
  openLogin: () => void;
  onLogout: () => void;
  onDeleteAccount: () => Promise<void>;
}

export default function AccountMenu({}: Props) {
  const [loginOpened, setLoginOpened] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const {user, loading, logout, deleteAccount} = useAuth();

  async function confirmedDelete() {
    await deleteAccount();
    setConfirmDeleteOpen(false);
  }

  return <>
    <LoginModal opened={loginOpened} onClose={() => setLoginOpened(false)} />

    <ConfirmationModal
      opened={confirmDeleteOpen}
      onClose={() => setConfirmDeleteOpen(false)}
      onConfirm={confirmedDelete}
      title="Are you sure?"
      buttonLabel="Delete Account"
    >
      <Text>This is permanent.</Text>
    </ConfirmationModal>

    {!user
      ? <Button loading={loading} onClick={() => setLoginOpened(true)}>Log In</Button>
      : <Menu withArrow shadow="md" transitionProps={{ transition: "scale" }}>
        <Menu.Target>
          <Button
            variant="subtle" size="lg" px="xs"
            leftSection={
              <ThemeIcon variant="outline" size="lg" bdrs="lg">
                {user?.is_superuser ? <IconUserBolt /> : <IconUser />}
              </ThemeIcon>
            }
          >
            <Stack gap={0} visibleFrom="sm">
              <Text size="sm">{user.full_name || (user.is_superuser && "Super " + "User")}</Text>  
              <Text size="sm" c="dimmed">{user.email}</Text>
            </Stack>              
          </Button>
        </Menu.Target>
        <Menu.Dropdown>
          {/* Menu Content */}
          <Menu.Item color="orange" onClick={logout} leftSection={<IconLogout />}>Log Out</Menu.Item>
          <Menu.Item color="red" onClick={() => setConfirmDeleteOpen(true)} leftSection={<IconTrash />}>Delete Account</Menu.Item>
        </Menu.Dropdown>
      </Menu>
    }
  </>;


  return !user
    ? <>
      <LoginModal opened={loginOpened} onClose={() => setLoginOpened(false)} />
      <Button loading={loading} onClick={() => setLoginOpened(true)}>Log In</Button>
    </>
    : <>
    <ConfirmationModal
      opened={confirmDeleteOpen}
      onClose={() => setConfirmDeleteOpen(false)}
      onConfirm={async () => {
        await deleteAccount();
        setConfirmDeleteOpen(false);
      }}
      loading={false}
      title="Are you sure?"
      buttonLabel="Delete Account"
    >
      <Text>This is permanent.</Text>
    </ConfirmationModal>

    <Menu shadow="md" withArrow offset={0} transitionProps={{ transition: "scale" }}>
      <Menu.Target>
        <Button 
          variant="subtle" size="lg" p={0}
          leftSection={
            <ThemeIcon variant="outline" size="lg" bdrs="lg">
              {user?.is_superuser ? <IconUserBolt /> : <IconUser />}
            </ThemeIcon>
          }
        >
          <Stack gap={0} visibleFrom="sm">
            <Text size="sm">{user.full_name || `${user.is_superuser ? "Super ": ""}User`}</Text>
            <Text size="xs" c="dimmed">{user.email}</Text>
          </Stack>
        </Button>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Item color="orange" onClick={logout}>Log Out</Menu.Item>

        <Menu.Divider />

        <Menu.Item color="red" onClick={() => setConfirmDeleteOpen(true)}>Delete Account</Menu.Item>
      </Menu.Dropdown>
    </Menu>
  </>;
}
