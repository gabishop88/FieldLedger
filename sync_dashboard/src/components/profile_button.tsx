import {
    Avatar,
    Button,
    Group,
    Menu,
    Modal,
    Skeleton,
    Stack,
    Text,
} from "@mantine/core";

import { type User } from "../api/auth";
import { useState } from "react";

interface Props {
    user: User | null;
    loading: boolean;
    onLogin: () => void;
    onLogout: () => void;
    onDeleteAccount: () => Promise<void>;
}

export default function AccountMenu({ user, loading, onLogin, onLogout, onDeleteAccount }: Props) {
    const [confirmOpen, setConfirmOpen] = useState(false);

    if (loading) return <Skeleton h={32} w={180} />;
    if (!user) return <Button onClick={onLogin}>Log In</Button>;
    return <>
        <Modal opened={confirmOpen} onClose={() => setConfirmOpen(false)} title="Are you sure?" centered size="xs">
            <Stack ms="auto">
                <Text>This is permanent.</Text>

                <Button color="red" onClick={async () => {
                    await onDeleteAccount();
                    setConfirmOpen(false);
                }}>Delete Account</Button>
            </Stack>
        </Modal>

        <Menu shadow="md">
            <Menu.Target>
                <Button variant="subtle" size="lg" px="sm">
                    <Group>
                        <Avatar radius="lg">
                            {user.full_name?.[0] ?? user.email[0].toUpperCase()}
                        </Avatar>

                        <div>
                            <Text size="sm">{user.full_name || `${user.is_superuser ? "Super ": ""}User`}</Text>
                            <Text size="xs" c="dimmed">{user.email}</Text>
                        </div>
                    </Group>
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
