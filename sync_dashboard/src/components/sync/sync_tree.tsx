import { Badge, Divider, getTreeExpandedState, Group, ScrollArea, Stack, Text, Tooltip, Tree, useTree, type BadgeProps, type RenderTreeNodePayload, type TreeNodeData } from "@mantine/core";

import { useEffect, useMemo } from "react";
import { isActive, SyncActions, SyncIcon } from "./status_info";
import type { SyncLink } from "../../types/fl";
import { IconListTree } from "@tabler/icons-react";

function compareActiveThenAlpha(a: SyncLink<"org" | "farm" | "field">, b: SyncLink<"org" | "farm" | "field">) {
  if (isActive(a) !== isActive(b)) return Number(isActive(b)) - Number(isActive(a));
  return a.data.name.localeCompare(b.data.name, undefined, { sensitivity: "base", numeric: true });
}

function linkAsTreeNode(node: SyncLink<"org" | "farm" | "field">): SyncTreeNodeData {
  const isField = node.table_name === "field";
  const children = node.children.filter(
    c => c.table_name === "org" || c.table_name === "farm" || c.table_name === "field"
  );

  return {
    label: (node.data.name as string | undefined) ?? node.uri,
    value: node.uri,
    linkData: node,
    children: isField ? undefined : children.sort(compareActiveThenAlpha).map(linkAsTreeNode),
  }
}

interface SyncTreeNodeData extends TreeNodeData {
  linkData: SyncLink<"org" | "farm" | "field">;
  children?: SyncTreeNodeData[];
}

// ------------------------------------------------------------------------------------------------
// #region ----------------------------------- ChildCountBadges -----------------------------------
// ------------------------------------------------------------------------------------------------

interface ChildCountBadgeData {
  countFn: (node: SyncTreeNodeData) => number;
  label?: string | ((count: number) => React.ReactNode);
  color?: BadgeProps["color"];
  variant?: BadgeProps["variant"];
  hidden?: (count: number) => boolean;
}

const CHILD_COUNT_BADGES: ChildCountBadgeData[] = [
  {
    countFn: n => n.children?.filter(c => isActive(c.linkData)).length ?? 0,
    label: "Active Child Links",
    variant: "outline",
  },
  {
    countFn: n => n.children?.filter(c => !isActive(c.linkData)).length ?? 0,
    label: "Inactive Child Links",
    variant: "default",
  },
  {
    countFn: n => n.linkData.children?.filter(c => c.table_name === "boundary").length ?? 0,
    label: "Field Boundaries",
    color: "blue",
    variant: "light",
  },
  {
    countFn: n => n.linkData.children?.filter(c => c.table_name === "field_op").length ?? 0,
    label: "Field Operations",
    color: "orange",
    variant: "light",
  },
  {
    countFn: n => n.linkData.children?.filter(c => c.table_name == "product").length ?? 0,
    label: "Products",
    color: "purple",
  }
];

function ChildCountBadges({ node }: { node: SyncTreeNodeData }) {
  return <>
    {CHILD_COUNT_BADGES.map(badge => {
      const value = badge.countFn(node);
      const labelText = typeof badge.label === "function" ? badge.label(value) : badge.label;
      const hide = badge.hidden?.(value) ?? value === 0;
      const id = `${node.value}:Count ${badge.label}`;
      return hide ? null : <Tooltip key={id} label={labelText} hidden={!labelText}>
        <Badge size="xs" pt={4} radius="sm" variant={badge.variant} color={badge.color}>
          {value}
        </Badge>
      </Tooltip>;
    })}
  </>;
}

// #endregion -------------------------------------------------------------------------------------
// #region ----------------------------------------- Leaf -----------------------------------------
// ------------------------------------------------------------------------------------------------

function Leaf({ tree, node, selected, elementProps }: RenderTreeNodePayload) {
  const syncNode = node as SyncTreeNodeData;
  const label = `${syncNode.linkData.status}${syncNode.linkData.local_persistent ? ", Persistent" : ""}`
  const selectable = isActive(syncNode.linkData) && syncNode.linkData.table_name === "field";

  return <Group wrap="nowrap" pt={2}>
    <Group
      {...elementProps}
      gap="xs" flex={1}
      onClick={e => {
        const prev = tree.selectedState;
        elementProps.onClick?.(e);
        tree.setSelectedState(selected ? [] : selectable ? [syncNode.value] : prev);
      }}
    >
      <Tooltip label={label}>
        <Group gap="xs">
          <SyncIcon status={syncNode.linkData.status} variant="subtle"/>
          <Text size="sm">{node.label}</Text>
        </Group>
      </Tooltip>

      <ChildCountBadges node={syncNode} />

      <Divider flex={1} variant="dashed" color="gray" />
    </Group>
    <SyncActions node={syncNode.linkData} />
  </Group>
}

// #endregion -------------------------------------------------------------------------------------
// #region --------------------------------------- SyncTree ---------------------------------------
// ------------------------------------------------------------------------------------------------

interface Props {
  trees: SyncLink<"org">[];
  selectedField: SyncLink<"field"> | null;
  onSelectField: (fieldUri: string | null) => void;
}

export default function SyncTree({ trees, selectedField, onSelectField }: Props) {
  const data = useMemo(() => trees.map(linkAsTreeNode), [trees]);
  const tree = useTree({
    initialExpandedState: getTreeExpandedState(data, "*"),
    initialSelectedState: selectedField ? [selectedField.uri] : [],
    onSelectedStateChange: ([uri]) => onSelectField(uri),
  });

  useEffect(() => {
    const expanded = getTreeExpandedState(data, "*");
    tree.setExpandedState({ ...expanded, ...tree.expandedState, });
  }, [data]);

  return <ScrollArea scrollbarSize={8} type="auto" dir="rtl">
    <Stack align="stretch" dir="ltr" p="sm">
      <Group justify="center">
        <IconListTree />
        <Text size="sm" ff="monospace">Organizations, Farms, and Fields</Text>
      </Group>

      <Group justify="space-between">
        <Text size="xs" ff="monospace">Status</Text>
        <Text size="xs" ff="monospace">Actions</Text>
      </Group>

      <Tree
        data={data} tree={tree}
        withLines selectOnClick
        renderNode={payload => <Leaf {...payload} />}
      />
    </Stack>
  </ScrollArea>
}
