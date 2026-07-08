import { Box, Center, Group, Modal, ScrollArea, Stack, Text } from "@mantine/core";
import { type SyncTreeNode } from "../api/jd";
import UpdateStatusButtons from "./status_buttons";

interface Props {
    boundary: SyncTreeNode | null;
    onClose: () => void;
}

export default function BoundaryModal({ boundary, onClose }: Props) {
    if (!boundary) return <Modal opened={false} onClose={onClose} />;

    return <Modal opened onClose={onClose} title="Boundary" size="80%">
        <Stack>
            <Center bd={1} bdrs={4} w="90%" >
                <Text c="dimmed">Map Placeholder</Text>
            </Center>

            <Box>
                <Text fw={600} mb="xs">Boundary Details</Text>

                <ScrollArea>
                    {JSON.stringify(boundary.data, null, 2)}
                </ScrollArea>
            </Box>

            <Group>
                <Text>Actions:</Text>
    
                <UpdateStatusButtons node={boundary} />
            </Group>
        </Stack>
    </Modal>
}
