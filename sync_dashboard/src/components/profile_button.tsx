import {
    Avatar,
    Button,
    Group,
    Menu,
    Skeleton,
    Text,
} from "@mantine/core";

import { type User } from "../api/auth";

interface Props {
    user: User | null;
    loading: boolean;
    onLogin: () => void;
    onLogout: () => void;
}

export default function AccountMenu({ user, loading, onLogin, onLogout }: Props) {
    if (loading) return <Skeleton h={32} w={180} />;
    if (!user) return <Button onClick={onLogin}>Log In</Button>;
    return (
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
                <Menu.Item color="red" onClick={onLogout}>Log Out</Menu.Item>
            </Menu.Dropdown>
        </Menu>
    );
}
