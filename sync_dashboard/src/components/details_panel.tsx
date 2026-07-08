import { Badge, Box, Card, Center, Divider, Group, ScrollArea, Scroller, Stack, Text, Textarea, Timeline } from "@mantine/core";
import { statusDetails, type SyncTreeNode } from "../api/jd";
import { useMemo, useState } from "react";
import UpdateStatusButtons from "./status_buttons";
import BoundaryModal from "./boundary_modal";

interface Props {
    field: SyncTreeNode | null;
    selectedOperation: SyncTreeNode | null;
    onSelectOperation: (op: SyncTreeNode | null) => void;
}

interface ChipProps {
    boundary: SyncTreeNode;
    onClick: () => void;
    children: React.ReactNode;
}

function BoundaryChip({ boundary, onClick, children }: ChipProps) {
    const statusInfo = statusDetails[boundary.status];
    return <Badge 
        leftSection={<statusInfo.icon size={18} color={statusInfo.color} />}
        onClick={onClick}
        variant="outline"
        size="lg"
        radius="md"
        color="blue"
    >
        {children}
    </Badge>
}


interface OpCardProps {
    op: SyncTreeNode;
    selected: boolean;
    onClick: () => void;
    children: React.ReactNode | null;
}

function TimelineOpCard({ op, selected, onClick, children }: OpCardProps) {
    const statusInfo = statusDetails[op.status];
    const title = `${op.data.cropSeason} ${op.data.fieldOperationType}`;
    const bullet = <statusInfo.icon color={statusInfo.color} size={16} />;

    return <Timeline.Item 
        key={op.uri}
        title={title}
        bullet={bullet}
        onClick={onClick}
        style={{ cursor: "pointer" }}
    >
        <Card withBorder={selected} p="xs">
            <Stack gap="xs">
                {children}
            </Stack>
        </Card>
    </Timeline.Item>
}

function EmptyFieldCard() {
    return <Center h="100%">
        <Card withBorder shadow="md" maw={420}>
            <Stack gap="xs" align="center">
                <Text fw={600}>
                    No Field Selected
                </Text>

                <Text c="dimmed" ta="center">
                    Select a synced field from the sync tree to browse
                    field operations and boundaries.
                </Text>
            </Stack>
        </Card>
    </Center>
}

export default function FieldDetailsPanel({ field, selectedOperation, onSelectOperation }: Props) {
    const [selectedBoundary, setSelectedBoundary] = useState<SyncTreeNode | null>(null);

    const boundaries = useMemo(
        () => field?.children.filter((c) => c.table_name == "boundary") ?? [],
        [field]
    );
    const operations = useMemo(
        () => field?.children.filter(
            (c) => c.table_name == "field_op"
        ).sort(
            (a, b) => Date.parse(String(a.data.startDate)) - Date.parse(String(b.data.startDate))
        ).reverse() ?? [],
        [field]
    );

    if (!field) return <EmptyFieldCard />
    return <>
        <BoundaryModal
            boundary={selectedBoundary}
            onClose={() => setSelectedBoundary(null)}
        />

        <Stack h="100%" gap={0}>
            <Group wrap="nowrap" align="stretch" mih={0}>
                <ScrollArea>
                    <Timeline>
                        {operations.map((op) => {
                            const selected = selectedOperation?.uri === op.uri;
                            const boundary = op.children?.find((c) => c.table_name === "boundary");

                            return <TimelineOpCard 
                                op={op}
                                selected={selected}
                                onClick={() => onSelectOperation(op)}
                            >
                                <Text size="xs" c="dimmed">
                                    {new Date(String(op.data.startDate ?? "")).toDateString()}
                                </Text>

                                {selected &&
                                    <Group flex={1} justify="space-around">
                                        <UpdateStatusButtons node={op} />

                                        {!!boundary &&
                                            <BoundaryChip
                                            boundary={boundary}
                                            onClick={() => setSelectedBoundary(boundary)}
                                            >
                                                Operation Boundary
                                            </BoundaryChip>
                                        }
                                    </Group>
                                }
                            </TimelineOpCard>
                        })}
                    </Timeline>
                </ScrollArea>

                <Divider orientation="vertical" />

                <Box p="md" flex={1} mih={0} style={{ overflow: "auto" }}>
                    {selectedOperation 
                        ? <Textarea 
                            readOnly
                            autosize
                            minRows={28}
                            value={JSON.stringify(selectedOperation.data, null, 2)}
                        />
                        : <Text c="dimmed">Select an operation.</Text>
                    }
                </Box>
            </Group>

            <Divider />

            <Group p="sm">
                <Text fw={600} mb="xs">Boundaries</Text>

                <Scroller>
                    {boundaries.map((boundary, ix) => 
                        <BoundaryChip 
                            key={boundary.uri}
                            boundary={boundary}
                            onClick={() => setSelectedBoundary(boundary)}
                        >
                            Field Boundary {ix + 1}
                        </BoundaryChip>
                    )}
                </Scroller>
            </Group>
        </Stack>
    </>
}
