import { Box, Button, Card, Center, Code, Divider, Group, ScrollArea, Scroller, Stack, Text, Timeline } from "@mantine/core";
import { useMemo, useState } from "react";
import UpdateStatusActions from "./status_actions";
import BoundaryModal from "./boundary_modal";
import type { JDBoundary, JDField, JDFieldOp } from "../../types/jd";
import type { SyncLink } from "../../types/fl";
import { statusDetails } from "./status_info";

interface ChipProps {
    boundary: SyncLink<JDBoundary>;
    onClick: () => void;
    children: React.ReactNode;
}

function BoundaryChip({ boundary, onClick, children }: ChipProps) {
    const statusInfo = statusDetails[boundary.status];
    return <Button 
        leftSection={<statusInfo.icon size={18} color={statusInfo.color} />}
        onClick={onClick}
        variant="outline"
        color="blue"
    >
        {children}
    </Button>
}


interface OpCardProps {
    op: SyncLink<JDFieldOp>;
    selected: boolean;
    onClick: () => void;
    children: React.ReactNode | null;
}

function TimelineOpCard({ op, selected, onClick, children }: OpCardProps) {
    const statusInfo = statusDetails[op.status];
    const opType = String(op.data.fieldOperationType);
    const title = `${op.data.cropSeason} ${opType[0].toUpperCase()}${opType.slice(1)}`;
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

interface Props {
    field: SyncLink<JDField> | null;
    selectedOperation: SyncLink<JDFieldOp> | null;
    onSelectOperation: (op: SyncLink<JDFieldOp> | null) => void;
}

export default function FieldDetailsPanel({ field, selectedOperation, onSelectOperation }: Props) {
    const [selectedBoundaryUri, setSelectedBoundaryUri] = useState<string | null>(null);
    const selectedBoundary = useMemo(
        () => !selectedBoundaryUri ? null : (
            field?.children.find(b => b.uri === selectedBoundaryUri) ??
            selectedOperation?.children.find(b => b.uri === selectedBoundaryUri)
        ) as SyncLink<JDBoundary> | null,
        [field, selectedOperation, selectedBoundaryUri]
    );

    const boundaries = useMemo(
        () => field?.children.filter((c): c is SyncLink<JDBoundary> => c.table_name == "boundary") ?? [],
        [field]
    );
    const operations = useMemo(
        () => field?.children.filter(
            (c): c is SyncLink<JDFieldOp> => c.table_name == "field_op"
        ).sort(
            (a, b) => Date.parse(String(a.data.startDate)) - Date.parse(String(b.data.startDate))
        ).reverse() ?? [],
        [field]
    );

    if (!field) return <EmptyFieldCard />
    return <>
        <BoundaryModal
            boundary={selectedBoundary}
            onClose={() => setSelectedBoundaryUri(null)}
        />

        <Stack h="100%" gap={0}>
            <Group wrap="nowrap" align="stretch" flex={1} mih={0}>
                <ScrollArea dir="rtl" scrollbarSize={5} px="xs">
                    <Timeline dir="ltr">
                        {operations.map((op) => {
                            const selected = selectedOperation?.uri === op.uri;
                            const boundary = op.children?.find((c): c is SyncLink<JDBoundary> => c.table_name === "boundary");

                            return <TimelineOpCard 
                                op={op}
                                selected={selected}
                                onClick={() => onSelectOperation(selected ? null : op)}
                            >
                                <Text size="xs" c="dimmed">
                                    {new Date(String(op.data.startDate ?? "")).toDateString()}
                                </Text>

                                {selected &&
                                    <Group flex={1} justify="space-around">
                                        <UpdateStatusActions node={op} />

                                        {!!boundary &&
                                            <BoundaryChip
                                            boundary={boundary}
                                            onClick={() => setSelectedBoundaryUri(boundary.uri)}
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
                        ? <Code bdrs="md" block>{JSON.stringify(selectedOperation.data, null, 2)}</Code>
                        : <Text c="dimmed">Select an operation.</Text>
                    }
                </Box>
            </Group>

            <Divider />

            <Group mt="lg" align="center">
                <Text fw={600}>{field.data.name} Boundaries:</Text>

                <Scroller>
                    {boundaries.map((boundary, ix) => 
                        <BoundaryChip 
                            key={boundary.uri}
                            boundary={boundary}
                            onClick={() => setSelectedBoundaryUri(boundary.uri)}
                        >
                            {boundary?.data.name ?? `Boundary ${ix + 1}`}
                        </BoundaryChip>
                    )}
                </Scroller>
            </Group>
        </Stack>
    </>
}
