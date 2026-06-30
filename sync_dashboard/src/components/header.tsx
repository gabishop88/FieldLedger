import { AppShell, Group, Title } from "@mantine/core";
import AccountMenu from "./profile_button"
import { type User } from "../api/auth";

interface Props {
    user: User | null;
    loading: boolean;
    onLogin: () => void;
    onLogout: () => void;
    onDeleteAccount: () => Promise<void>;
}

export default function AppHeader({ user, loading, onLogin, onLogout, onDeleteAccount }: Props) {
    return (
        <AppShell.Header p="lg">
            <Group justify="space-between" align="end">
                <Title>
                    FieldLedger Sync
                </Title>

                <AccountMenu
                    user={user}
                    loading={loading}
                    onLogin={onLogin}
                    onLogout={onLogout}
                    onDeleteAccount={onDeleteAccount}
                />
            </Group>
        </AppShell.Header>
    );
}
