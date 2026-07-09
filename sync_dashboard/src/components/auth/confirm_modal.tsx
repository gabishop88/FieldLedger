import { Button, Group, Modal, Stack } from "@mantine/core";
import type { ReactNode } from "react";

interface ConfirmModalProps {
    opened: boolean;
    onClose: () => void;
    onConfirm: () => void;
    loading: boolean;

    title: ReactNode;
    children: ReactNode;
    buttonLabel?: string;
}

export default function ConfirmModal({
    opened, onClose, onConfirm, loading, title, children, buttonLabel = "Confirm"
}: ConfirmModalProps) {
    return <Modal opened={opened} onClose={onClose} title={title} transitionProps={{ transition: 'fade-down' }}>
        <Stack>
            {children}

            <Group justify="space-between">
                <Button variant="default" onClick={onClose}>Cancel</Button>
                <Button color="red" loading={loading} onClick={() => {
                    onConfirm();
                    onClose();
                }}>{buttonLabel}</Button>

            </Group>
        </Stack>
    </Modal>
}
