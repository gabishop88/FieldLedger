import {
    Anchor,
    Button,
    Group,
    Modal,
    PasswordInput,
    Stack,
    TextInput,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useAuth } from "../hooks/use_auth";
import { useState } from "react";

interface Props {
    opened: boolean;
    onClose: () => void;
}

type Mode = "login" | "register";

export default function LoginModal({ opened, onClose }: Props) {
    const { login, register } = useAuth();
    const [mode, setMode] = useState<Mode>("login");
    const form = useForm({
        initialValues: { email: "", password: "", confirm: "", full_name: "" },
        validate: { confirm: (value, values) => mode === "register" && value !== values.password ? "Passwords do not match" : null }
    });

    const toggleMode = () => setMode((m) => m === "login" ? "register" : "login");

    async function handleSubmit(values: typeof form.values) {
        mode === "login"
            ? await login({ username: values.email, password: values.password })
            : await register({ email: values.email, password: values.password, full_name: values.full_name });
        onClose();
    }

    return (
        <Modal opened={opened} onClose={onClose} title="FieldLedger Account">
            <form onSubmit={form.onSubmit(handleSubmit)}>
                <Stack>
                    <TextInput
                        label="Email"
                        autoComplete="username"
                        {...form.getInputProps("email")}
                    />

                    <PasswordInput
                        label="Password"
                        autoComplete={mode === "login" ? "current-password" : "new-password"}
                        {...form.getInputProps("password")}
                    />

                    {mode === "register" && <>
                        <PasswordInput
                            label="Confirm Password"
                            autoComplete="new-password"
                            {...form.getInputProps("confirm")}
                        />

                        <TextInput
                            label="Full Name"
                            autoComplete="name"
                            {...form.getInputProps("full_name")}
                        />
                    </>}

                    <Button type="submit">{mode === "login" ? "Log In" : "Create Account"}</Button>

                    <Group justify="center">
                        <Anchor component="button" type="button" onClick={toggleMode} >
                            {mode === "login" ? "Create account" : "Back to login"}
                        </Anchor>
                    </Group>
                </Stack>
            </form>
        </Modal>
    );
}
