import { Badge, Divider, Group, ScrollArea, Text, Tooltip, Tree, type TreeNodeData } from "@mantine/core";

import { useMemo } from "react";
import { statusDetails } from "./status_info";
import UpdateStatusActions from "./status_actions";
import type { SyncLink } from "../../types/fl";
import type { JDFarm, JDField, JDOrg } from "../../types/jd";

interface Props {
    trees: SyncLink<JDOrg>[];

    selectedField: SyncLink<JDField> | null;
    onSelectField: (field: SyncLink<JDField> | null) => void;
}

interface SyncTreeNodeData extends TreeNodeData {
    syncNode: SyncLink<JDOrg | JDFarm | JDField>;
    children?: SyncTreeNodeData[];
}

function convertTree(node: SyncLink<JDOrg | JDFarm | JDField>): SyncTreeNodeData {
    const isField = node.table_name === "field";
    const children = node.children as SyncLink<JDOrg | JDFarm | JDField>[];

    return {
        label: (node.data.name as string | undefined) ?? node.id,
        value: node.id,
        children: isField ? undefined : children.map(convertTree).reverse(),
        syncNode: node,
    }
}

function countChildren(node: SyncTreeNodeData) {
    return {
        total: node.children?.length,
        active: node.children?.filter(
            (child) => statusDetails[child.syncNode.status].active
        ).length,
        inactive: node.children?.filter(
            (child) => !statusDetails[child.syncNode.status].active
        ).length,
        boundaries: node.syncNode.children?.filter(
            (child) => child.table_name === "boundary"
        ).length,
        operations: node.syncNode.children?.filter(
            (child) => child.table_name === "field_op"
        ).length,
    }
}


export default function SyncTree({ trees, selectedField, onSelectField }: Props) {
    const data = useMemo(() => trees.map(convertTree), [trees]);
    return <ScrollArea offsetScrollbars>
        <Tree
            data={data}
            selectOnClick={false}
            renderNode={({ node, elementProps }) => {
                const nodeData = (node as SyncTreeNodeData).syncNode;
                const statusInfo = statusDetails[nodeData.status];
                const childCounts = countChildren(node as SyncTreeNodeData);
                const selected = selectedField?.uri === nodeData.uri;
                const isField = nodeData.table_name === "field";

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
                            if (isField && statusInfo.active) onSelectField(selected ? null : nodeData as SyncLink<JDField>);
                        }}
                    >
                        <Tooltip label={`${nodeData.status}${nodeData.local_persistent ? ", Persistent" : ""}`}>
                            <Group gap="xs" align="flex-start">
                                <statusInfo.icon size={18} color={statusInfo.color} />

                                <Text size="sm">{node.label}</Text>
                            </Group>
                        </Tooltip>

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

                        <Divider flex={1} variant="dashed" />
                    </Group>

                    <UpdateStatusActions node={nodeData} />
                </Group>
            }}
        />
    </ScrollArea>
}
