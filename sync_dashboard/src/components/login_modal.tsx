import {
    Button,
    Modal,
    PasswordInput,
    Stack,
    TextInput,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useAuth } from "../hooks/use_auth";

interface Props {
    opened: boolean;
    onClose: () => void;
}

export default function LoginModal({ opened, onClose }: Props) {
    const { login } = useAuth();
    const form = useForm({ initialValues: {username: "", password: ""}});

    async function handleSubmit(values: typeof form.values) {
        await login(values);
        onClose();
    }

    return (
        <Modal opened={opened} onClose={onClose} title="FieldLedger Login">
            <form onSubmit={form.onSubmit(handleSubmit)}>
                <Stack>
                    <TextInput
                        label="Email"
                        autoComplete="username"
                        {...form.getInputProps("username")}
                    />

                    <PasswordInput
                        label="Password"
                        autoComplete="current-password"
                        {...form.getInputProps("password")}
                        />

                    <Button type="submit">Login</Button>
                </Stack>
            </form>
        </Modal>
    );
}
