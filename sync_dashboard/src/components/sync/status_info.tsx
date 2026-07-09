import { Button, Group, HoverCard, Stack, Table, Text, Title } from "@mantine/core";
import { IconAlertTriangleFilled, IconCircleCheckFilled, IconCircleDashedCheck, IconInfoCircle, IconLockFilled, IconPlayerPauseFilled } from "@tabler/icons-react";
import type { SyncStatus, SyncStatusDetails } from "../../types/fl";

export const statusDetails: Record<SyncStatus, SyncStatusDetails> = {
    Synced: {
        color: "green",
        icon: IconCircleCheckFilled,
        description: "Resource linked; up to date.",
        transitions: {
            Paused: "Keep Link, stop recieving updates from John Deere.",
            Unsynced: "Remove children and linked data. If data is needed outside of sync, status will be set to 'Paused' but will still try to remove children.",
        },
        active: true,
    },
    Pending: {
        color: "yellow",
        icon: IconCircleCheckFilled,
        description: "Resource linked; not up to date.",
        transitions: {
            Synced: "In case it has been pending for too long, attempt to resync manually.",
            Unsynced: "In case it has been pending for too long, give up and unsync.",
        },
        active: true,
    },
    Paused: {
        color: "orange",
        icon: IconPlayerPauseFilled,
        description: "Resource linked; updates paused.",
        transitions: {
            Synced: "Keep link and resume updates from John Deere.",
            Unsynced: "Attempt to remove link and unsync children.",
        },
        active: true,
    },
    Unsynced: {
        color: "gray",
        icon: IconCircleDashedCheck,
        description: "Resource discovered; not linked.",
        transitions: {
            Synced: "Start Sync Process. Look for matching records or create one.",
        },
        active: false,
    },
    Inaccessible: {
        color: "red",
        icon: IconAlertTriangleFilled,
        description: "Organization discovered; access not enabled.",
        transitions: {
            Unsynced: "If you have enabled access to this org, click to try to clear error status.",
        },
        active: false,
    },
    Conflict: {
        color: "dark",
        icon: IconLockFilled,
        description: "Organization discovered; linked by another user.",
        transitions: {
            Unsynced: "Attempt to sync, only works if there are no other users syncing this org.",
        },
        active: false,
    },
}

export default function SyncStatusHelp() {
    return <HoverCard width={900} shadow="md" position="right-end">
        <HoverCard.Target>
            <Button variant="transparent" size="xs">
                <IconInfoCircle size={22} />
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
                                                    <Target.icon size={16} color={Target.color} />

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