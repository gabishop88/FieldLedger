import { Button, Group, HoverCard, Stack, Table, Text, Title } from "@mantine/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { statusDetails, type SyncStatus } from "../api/jd";

export default function SyncStatusHelp() {
    return <HoverCard width={900} shadow="md" position="right-end">
        <HoverCard.Target>
            <Button variant="transparent" size="sm">
                <IconInfoCircle size={24} />
            </Button>
        </HoverCard.Target>

        <HoverCard.Dropdown>
            <Stack gap="sm">
                <Title order={5}>Sync Status Guide</Title>

                <Table withTableBorder highlightOnHover>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th>Status</Table.Th>
                            <Table.Th>Description</Table.Th>
                            <Table.Th>Availble Actions</Table.Th>
                        </Table.Tr>
                    </Table.Thead>

                    <Table.Tbody>
                        {(Object.entries(statusDetails) as [
                                SyncStatus, typeof statusDetails[SyncStatus]
                        ][]).map(
                            ([ statusName, info ]) => <Table.Tr key={statusName}>
                                <Table.Td>
                                    <Group gap="xs" wrap="nowrap">
                                        <info.icon size={16} color={info.color} />
                                        <Text>{statusName}</Text>
                                    </Group>
                                </Table.Td>

                                <Table.Td>
                                    <Text size="sm">{info.description}</Text>
                                </Table.Td>

                                <Table.Td>
                                    <Stack gap={4}>
                                        {Object.entries(info.transitions).map(
                                            ([ toStatus, actioninfo]) => {
                                                const Target = statusDetails[toStatus as SyncStatus];
                                                return <Group key={toStatus} gap="xs" wrap="nowrap">
                                                    <Target.icon size={14} color={Target.color} />

                                                    <Text size="sm">
                                                        <b>{toStatus}</b>{" - "}{actioninfo}
                                                    </Text>
                                                </Group>
                                            }
                                        )}
                                    </Stack>
                                </Table.Td>
                            </Table.Tr>
                        )}
                    </Table.Tbody>
                </Table>
            </Stack>
        </HoverCard.Dropdown>
    </HoverCard>;
}