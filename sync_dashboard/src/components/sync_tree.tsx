import { Stack, Text } from "@mantine/core";

import { type SyncTreeNode } from "../api/jd";

interface Props {
    trees: SyncTreeNode[];
}

function Node({ node, depth = 0 }: { node: SyncTreeNode; depth?: number; }) {
    return (
        <>
            <Text pl={depth * 18} py={3}>{node.data.name as string ?? node.uri}</Text>
            {node.children?.map((child) => <Node key={child.id} node={child} depth={depth + 1} />)}
        </>
    );
}

export default function SyncTree({ trees }: Props) {
    return (
        <Stack gap={2}>
            {trees.map((tree) => <Node key={tree.id} node={tree} />)}
        </Stack>
    );
}
