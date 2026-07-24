import { Button, Menu, Stack, Text, ThemeIcon } from "@mantine/core";

import { useState } from "react";
import ConfirmationModal from "./confirm_modal";
import type { User } from "../../types/fl";
import { IconUser, IconUserBolt } from "@tabler/icons-react";

interface Props {
  user: User | null;
  loading: boolean;
  onLogin: () => void;
  onLogout: () => void;
  onDeleteAccount: () => Promise<void>;
}

export default function AccountMenu({ user, loading, onLogin, onLogout, onDeleteAccount }: Props) {
  const [confirmOpen, setConfirmOpen] = useState(false);

  return !user 
    ? <Button loading={loading} onClick={onLogin}>Log In</Button>
    : <>
    <ConfirmationModal
      opened={confirmOpen}
      onClose={() => setConfirmOpen(false)}
      onConfirm={async () => {
        await onDeleteAccount();
        setConfirmOpen(false);
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
        <Menu.Item color="orange" onClick={onLogout}>Log Out</Menu.Item>

        <Menu.Divider />

        <Menu.Item color="red" onClick={() => setConfirmOpen(true)}>Delete Account</Menu.Item>
      </Menu.Dropdown>
    </Menu>
  </>;
}
