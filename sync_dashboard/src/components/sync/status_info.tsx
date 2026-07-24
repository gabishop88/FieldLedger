import { ActionIcon, Button, Group, HoverCard, Stack, Table, Text, ThemeIcon, Title, Tooltip, type ActionIconProps, type ThemeIconProps } from "@mantine/core";
import { IconAlertTriangleFilled, IconCircleCheckFilled, IconCircleDashedX, IconInfoCircle, IconLockFilled, IconPlayerPauseFilled } from "@tabler/icons-react";
import type { AnySyncLink, SyncStatus, SyncStatusDetails } from "../../types/fl";
import { useEffect, useState } from "react";
import { useSyncTree, useUpdateSync } from "../../hooks/use_sync_tree";

export const statusDetails: Record<SyncStatus, SyncStatusDetails> = {
  Synced: {
    color: "green",
    icon: IconCircleCheckFilled,
    description: "Resource linked; up to date.",
    transitions: {
      Paused: "Keep Link, stop recieving updates from John Deere.",
      Unsynced: "Unsync children, then remove link and linked data (unless data is needed elsewhere).",
    },
    active: true,
  },
  Pending: {
    color: "yellow",
    icon: IconCircleCheckFilled,
    description: "Resource linked; not up to date.",
    transitions: {
      Synced: "Try Refreshing First. If it has been pending for too long, click to resync manually.",
      Unsynced: "Try Refreshing First. If it has been pending for too long, click to unsync completely.",
    },
    active: true,
  },
  Paused: {
    color: "yellow",
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
    icon: IconCircleDashedX,
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

export function isActive(link: AnySyncLink): boolean {
  return statusDetails[link.status].active;
}

// ------------------------------------------------------------------------------------------------
// #region --------------------------------------- SyncIcon ---------------------------------------
// ------------------------------------------------------------------------------------------------

interface SyncIconProps {
  status: SyncStatus;
  size?: ThemeIconProps["size"];
  variant?: ThemeIconProps["variant"];
}

export function SyncIcon({ status, size="sm", variant="subtle" }: SyncIconProps) {
  const info = statusDetails[status];
  return <ThemeIcon size={size} variant={variant}  c={info.color}>
    <info.icon />
  </ThemeIcon>;
}

// #endregion -------------------------------------------------------------------------------------
// #region ------------------------------------- SyncActions --------------------------------------
// ------------------------------------------------------------------------------------------------

interface SyncActionsProps {
  node: AnySyncLink;
  size?: ActionIconProps["size"];
  variant?: ActionIconProps["variant"];
}

export function SyncActions({ node, size="sm", variant="light" }: SyncActionsProps) {
  const { isFetching } = useSyncTree(true);
  const [disabledBtns, setDisabledBtns] = useState(new Set<string>());
  useEffect(() => setDisabledBtns(prev => isFetching ? prev : new Set()), [isFetching]);

  const { mutate } = useUpdateSync();
  const keyFn = (status: SyncStatus) => `${node.uri}:${status}`;
  function updateStatus(to: SyncStatus) {
    setDisabledBtns(prev => {
      if (!prev.has(keyFn(to))) mutate({ uri: node.uri, newStatus: to });
      return prev.has(keyFn(to)) ? prev : new Set(prev).add(keyFn(to));
    });
  }

  const actions = Object.entries(statusDetails[node.status].transitions) as [SyncStatus, string][];
  return <Group gap={2} wrap="nowrap">
    {actions.map(([targetStatus, actionLabel]) => {
      const info = statusDetails[targetStatus];
      return <Tooltip key={keyFn(targetStatus)} label={actionLabel} position="right">
        <ActionIcon
          size={size}
          variant={variant}
          color={info.color}
          disabled={disabledBtns.has(keyFn(targetStatus))}
          onClick={() => updateStatus(targetStatus)}
        >
          <info.icon />
        </ActionIcon>
      </Tooltip>;
    })}
  </Group>;
}

// #endregion -------------------------------------------------------------------------------------
// #region ------------------------------------ SyncStatusHelp ------------------------------------
// ------------------------------------------------------------------------------------------------

export default function SyncStatusHelp() {
  const entries = Object.entries(statusDetails) as [SyncStatus, SyncStatusDetails][];
  return <HoverCard width={900} shadow="md" position="right-end" transitionProps={{ transition: "scale-x"}} withArrow>
    <HoverCard.Target>
      <Button variant="transparent" size="xs">
        <IconInfoCircle size={22} />
      </Button>
    </HoverCard.Target>

    <HoverCard.Dropdown>
      <Stack gap="sm">
        {/* TODO: organize and improve my instructions. */}
        <Title order={5}>Sync Guide</Title>
        <Text>
          'Syncing' means taking the record that is shown on this page, which comes from John Deere,
          and creating a copy of that record in the FieldLedger database. This copy will be kept up-to-date
          whenever changes are made to it in John Deere's Operations Center.
        </Text>
        <Text>The status symbols below are the <Text span fw="bold">most important</Text> part of the dashboard.</Text>
        <Text>They represent either the current sync status of an object, or an action to update the status.</Text>
        <Text>
          The tree on the left shows the Organizations, Farms, and Fields that you have access to from John Deere.
          You can see the current sync status on the left, and actions to update the status on the right.
          Once you sync an object in this tree, it will search for objects to fill out the next layer
          (organizations search for farms, farms for fields, etc.), and expand the tree. If the tree does not update,
          try clicking on the newly synced object or using the refresh button at the top.
        </Text>
        <Text>
          Each synced item in the tree also has numbered badges that count different types of discovered children.
        </Text>
        <Text>
          Once you have discovered one or more <Text span fw="bold">Fields</Text>, you may click on them to bring up 
          a list of Field Boundaries across the top, and Field Operations as a timeline that you can choose to sync.
        </Text>
        <Text>If you sync an operation, it will make the products and equipment used available for your Organization.</Text>

        <Table withTableBorder highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Status</Table.Th>
              <Table.Th>Description</Table.Th>
              <Table.Th>Availble Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {entries.map(([ status, { description, transitions} ]) => 
              <Table.Tr key={status}>
                <Table.Td>
                  <Group gap="xs" wrap="nowrap">
                    <SyncIcon status={status} />
                    <Text>{status}</Text>
                  </Group>
                </Table.Td>

                <Table.Td>
                  <Text size="sm">{description}</Text>
                </Table.Td>

                <Table.Td>
                  <Stack gap={4}>
                    {Object.entries(transitions).map(([ toStatus, actionInfo]) => 
                      <Group key={toStatus} gap="xs" wrap="nowrap">
                        <SyncIcon status={toStatus as SyncStatus} size="xs" variant="light"/>

                        <Text size="sm">
                          <Text span fw="bold">{toStatus}</Text>
                          {" - "}{actionInfo}
                        </Text>
                      </Group>
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