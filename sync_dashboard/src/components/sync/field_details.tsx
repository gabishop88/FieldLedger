import { Button, Card, Divider, Group, ScrollArea, Scroller, Stack, Text, Timeline } from "@mantine/core";
import { useMemo, useRef, useState } from "react";

import BoundaryModal from "./boundary_modal";
import type { SyncLink } from "../../types/fl";
import { isActive, SyncActions, SyncIcon } from "./status_info";
import OperationDetails from "./op_details";
import { EmptyOpCard } from "../instruction_cards";
import { useUpdateSync } from "../../hooks/use_sync_tree";

function opTitle(op: SyncLink<"field_op"> | null): string {
  if (!op) return "";
  const opType = String(op.data.fieldOperationType);
  return `${op.data.cropSeason} ${opType[0].toUpperCase()}${opType.slice(1)}`;
}

// ------------------------------------------------------------------------------------------------
// #region ------------------------------------- BoundaryChip -------------------------------------
// ------------------------------------------------------------------------------------------------

interface ChipProps {
  boundary: SyncLink<"boundary">;
  onClick: () => void;
  children?: React.ReactNode;
}

function BoundaryChip({ boundary, onClick, children }: ChipProps) {
  return <Button
    variant="outline"
    color="blue"
    onClick={onClick} 
    size="sm"
    leftSection={<SyncIcon status={boundary.status} size="xs" />}
  >
    {children}
  </Button>;
}

// #endregion -------------------------------------------------------------------------------------
// #region ------------------------------------- TimelineCard -------------------------------------
// ------------------------------------------------------------------------------------------------

interface TimelineCardProps {
  op: SyncLink<"field_op">;
  selected: boolean;
  onClick: () => void;
  children?: React.ReactNode | null;
}

function TimelineOpCard({ op, selected, onClick, children }: TimelineCardProps) {
  return <Timeline.Item
    key={op.uri}
    style={{ cursor: "pointer" }}
    title={opTitle(op)}
    onClick={onClick}
    bullet={<SyncIcon status={op.status} size="xs" />}
  >
    <Card withBorder={selected} p="xs">
      <Group justify="center">
        {children}
      </Group>
    </Card>
  </Timeline.Item>;
}

// #endregion -------------------------------------------------------------------------------------
// #region ---------------------------------- FieldDetailsPanel -----------------------------------
// ------------------------------------------------------------------------------------------------

interface Props {
  field: SyncLink<"field"> | null;
  selectedOp: SyncLink<"field_op"> | null;
  onSelectOp: (opUri: string | null) => void;
}

export default function FieldDetailsPanel({ field, selectedOp: selOp, onSelectOp }: Props) {
  const [pointerTop, setPointerTop] = useState<boolean | null>(null);
  const dividerRef = useRef<HTMLHRElement>(null);
  const dividerY = dividerRef.current?.getBoundingClientRect().top;

  const sortOps = (a: SyncLink<"field_op">, b: SyncLink<"field_op">) => b.data.startDate.localeCompare(a.data.startDate);
  const boundaries = useMemo(() => field?.children.filter(c => c.table_name === "boundary") ?? [], [field]);
  const ops = useMemo(() => field?.children.filter(c => c.table_name === "field_op").toSorted(sortOps) ?? [], [field]);
  const opBoundary = selOp?.children?.find(c => c.table_name === "boundary");
  const syncableOps = ops.filter(op => !isActive(op)).length;

  const [selectedBoundaryUri, setSelectedBoundaryUri] = useState<string | null>(null);
  const selectedBoundary = selectedBoundaryUri 
    ? boundaries.find(c => c.uri === selectedBoundaryUri)
    ?? (opBoundary?.uri === selectedBoundaryUri ? opBoundary : null) : null;

  // Either here or in request Fn, I need to rate limit or something because this sends too many requests too fast.
  // Or, I could make another endpoint to bulk sync/unsync by field?
  const { mutate, isPending } = useUpdateSync();
  const syncAll = () => ops
    .filter(op => !isActive(op))
    .forEach(op => mutate({ uri: op.uri, newStatus: "Synced" }));
  
  return <>
    <BoundaryModal boundary={selectedBoundary} onClose={() => setSelectedBoundaryUri(null)}/>

    <Stack
      h="100%"
      onPointerLeave={() => setPointerTop(null)}
      onPointerMove={e => setPointerTop(!dividerY ? null : e.clientY < dividerY)}
    >
      {/* Chips to Open BoundaryModal to sync Boundaries */}
      <Group gap="sm">
        <Card withBorder p="sm">
          <Text fw={600}>{field?.data.name} Boundaries:</Text>
          <Scroller>
            {boundaries.map((boundary, ix) => 
              <BoundaryChip key={boundary.uri} boundary={boundary} onClick={() => setSelectedBoundaryUri(boundary.uri)}>
                {boundary?.data.name ?? `Boundary ${ix + 1} (unnamed)`}
              </BoundaryChip>
            )}
          </Scroller>
        </Card>

        {opBoundary && 
          <Card withBorder p="sm">
            <Text fw={600}>{opTitle(selOp)} Boundary:</Text>

            <BoundaryChip key={opBoundary.uri} boundary={opBoundary} onClick={() => setSelectedBoundaryUri(opBoundary.uri)}>
              {opBoundary.data.name ?? `Operation Boundary`}
            </BoundaryChip>
          </Card>
        }
      </Group>

      {/* Divider highlights whether cursor is over top (boundary) or bottom (operations) section. */}
      <Stack gap={0}>
        <Text size="xs" pl="md" fw={pointerTop ? "bold" : "normal"} ff="monospace">Boundaries</Text>
        <Divider ref={dividerRef} />
        <Text size="xs" pl="md" fw={pointerTop === false  ? "bold" : "normal" } ff="monospace">Operations</Text>
      </Stack>

      {/* Operation Timeline and details when an op is selected. */}
      <Group flex={1} mih={0}>
        <Card withBorder py={0} pl={0} h="100%">
          <ScrollArea type="never" pl="sm">
            <Stack pt="sm">
              <Button 
                fullWidth
                variant="light"
                size="compact-sm"
                leftSection={<SyncIcon status="Synced"/>}
                disabled={!syncableOps}
                loading={isPending}
                onClick={syncAll}
              >
                Sync {syncableOps} Operation(s)
              </Button>
              <Timeline>
                {ops.map(op =>
                  <TimelineOpCard op={op} selected={selOp?.uri === op.uri} onClick={() => onSelectOp(selOp?.uri === op.uri ? null : op.uri)}>
                    <Text size="xs" c="dimmed">{new Date(String(op.data.startDate)).toDateString()}</Text>
                    {selOp?.uri === op.uri && <SyncActions node={op} />}
                  </TimelineOpCard>
                )}
              </Timeline>
            </Stack>
          </ScrollArea>
        </Card>

        <Card withBorder h="100%" flex={1} p={0}>
          {
            !selOp ? <EmptyOpCard /> :
            <OperationDetails selectedOp={selOp} title={opTitle(selOp)}/>
          }
        </Card>
      </Group>
    </Stack>
  </>;
}

// #endregion -------------------------------------------------------------------------------------
// ------------------------------------------------------------------------------------------------
