import { Badge, Button, Divider, Group, Stack, Text, Tooltip, Tree, type TreeNodeData } from "@mantine/core";

import { statusDetails, type SyncTreeNode } from "../api/jd";
import { useSyncTree } from "../hooks/use_sync_tree";
import { useMemo } from "react";
import { IconRefresh } from "@tabler/icons-react";
import SyncStatusHelp from "./status_helpcard";
import UpdateStatusButtons from "./status_buttons";

interface Props {
    trees: SyncTreeNode[];

    selectedField: SyncTreeNode | null;
    onSelectField: (field: SyncTreeNode | null) => void;
}

interface SyncTreeData extends TreeNodeData {
    syncNode: SyncTreeNode;
    children?: SyncTreeData[];
}

function convertTree(node: SyncTreeNode): SyncTreeData {
    const isField = node.table_name === "field";
    return {
        label: (node.data.name as string | undefined) ?? node.id,
        value: node.id,
        children: isField ? undefined : node.children?.map(convertTree).reverse(),
        syncNode: node,
    }
}

function countChildren(node: SyncTreeData) {
    return {
        total: node.children?.length,
        active: node.children?.filter(
            (child) => statusDetails[child.syncNode.status].active
        ).length,
        inactive: node.children?.filter(
            (child) => !statusDetails[child.syncNode.status].active
        ).length,
        boundaries: node.syncNode.children?.filter(
            (child) => child.data?.table_name === "boundary"
        ).length,
        operations: node.syncNode.children?.filter(
            (child) => child.data?.table_name === "field_op"
        ).length,
    }
}


export default function SyncTree({ trees, selectedField, onSelectField }: Props) {
    const { refetch, isFetching } = useSyncTree(true);
    const data = useMemo(() => trees.map(convertTree), [trees]);

    return <Stack gap="xs">
        <Group justify="space-between">
            <Tooltip label="Refresh">
                <Button 
                    size="xs"
                    variant="outline"
                    onClick={async () => await refetch()}
                    loading={isFetching}
                >
                    <IconRefresh size={18} />
                </Button>
            </Tooltip>

            <SyncStatusHelp />
        </Group>

        <Divider />

        <Tree
            data={data}
            selectOnClick={false}
            renderNode={({ node, elementProps }) => {
                const syncNode = (node as SyncTreeData).syncNode;
                const statusInfo = statusDetails[syncNode.status];
                const childCounts = countChildren(node as SyncTreeData);
                const selected = selectedField?.uri === syncNode.uri;
                const isField = syncNode.table_name === "field";

                return <Group justify="space-between" wrap="nowrap" w="100%">
                    <Group
                        gap="xs"
                        wrap="nowrap"
                        align="center"
                        flex={1}
                        {...elementProps}
                        style={{
                            cursor: !isField || statusInfo.active ? "pointer" : "default",
                            backgroundColor: selected ? "var(--mantine-color-blue-light)" : undefined,
                        }}
                        onClick={(event) => {
                            elementProps.onClick?.(event);
                            if (isField && statusInfo.active) onSelectField(selected ? null : syncNode);
                        }}
                    >
                        <Tooltip label={`${syncNode.status}${syncNode.local_persistent ? ", Persistent" : ""}`}>
                            <Group gap="xs" align="flex-start">
                                <statusInfo.icon size={18} color={statusInfo.color} />

                                <Text size="sm">{node.label}</Text>
                            </Group>
                        </Tooltip>

                        {!!childCounts.total && <>
                            {!!childCounts.active &&
                                <Tooltip label="Active Child Links">
                                    <Badge size="xs" pt={4} radius="sm" variant="outline">
                                        {childCounts.active}
                                    </Badge>
                                </Tooltip>
                            }
                            {!!childCounts.inactive &&
                                <Tooltip label="Inactive Child Links">
                                    <Badge size="xs" pt={4} radius="sm" variant="default">
                                        {childCounts.inactive}
                                    </Badge>
                                </Tooltip>
                            }
                            {!!childCounts.boundaries &&
                                <Tooltip label="Field Boundaries">
                                    <Badge size="xs" pt={4} radius="sm" color="blue" variant="light">
                                        {childCounts.boundaries}
                                    </Badge>
                                </Tooltip>
                            }
                            {!!childCounts.operations &&
                                <Tooltip label="Field Operations">
                                    <Badge size="xs" pt={4} radius="sm" color="orange" variant="light">
                                        {childCounts.operations}
                                    </Badge>
                                </Tooltip>
                            }
                        </>}

                        <Divider flex={1} variant="dashed" />
                    </Group>

                    <UpdateStatusButtons node={syncNode} />
                </Group>
            }}
        />
    </Stack>;
}
