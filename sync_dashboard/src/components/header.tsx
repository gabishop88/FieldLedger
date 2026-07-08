import { ActionIcon, AppShell, Box, Group, Title, useMantineColorScheme } from "@mantine/core";
import AccountMenu from "./profile_button"
import { type User } from "../api/auth";
import { IconMoonFilled, IconSunFilled } from "@tabler/icons-react";

interface Props {
    user: User | null;
    loading: boolean;
    onLogin: () => void;
    onLogout: () => void;
    onDeleteAccount: () => Promise<void>;
}

export default function AppHeader({ user, loading, onLogin, onLogout, onDeleteAccount }: Props) {
    const { toggleColorScheme } = useMantineColorScheme();

    return (
        <AppShell.Header p="lg">
            <Group justify="space-between" align="end">
                <Title pl="xl">
                    FieldLedger Sync
                </Title>

                <Group pr="xl">
                    <ActionIcon 
                        onClick={toggleColorScheme} 
                        variant="default" 
                        size="xl"
                        aria-label="Toggle color scheme"
                    >
                        <Box lightHidden><IconSunFilled /></Box>
                        <Box darkHidden><IconMoonFilled /></Box>
                    </ActionIcon>

                    <AccountMenu
                        user={user}
                        loading={loading}
                        onLogin={onLogin}
                        onLogout={onLogout}
                        onDeleteAccount={onDeleteAccount}
                    />
                </Group>
            </Group>
        </AppShell.Header>
    );
}
