import { ActionIcon, Group, Tooltip } from "@mantine/core";
import { useSyncTree, useUpdateSync } from "../../hooks/use_sync_tree";
import { useEffect, useState } from "react";
import type { SyncStatus, SyncLink } from "../../types/fl";
import { statusDetails } from "./status_info";

interface Props {
    node: SyncLink;
}

export default function UpdateStatusActions({ node }: Props) {
    const { mutate } = useUpdateSync();
    const { isFetching } = useSyncTree(true);
    const [disabledButtons, setDisabledButtons] = useState(new Set<string>());

    const transitions = statusDetails[node.status].transitions;
    
    function buttonClick(uri: string, newStatus: SyncStatus) {
        const key = `${uri}:${newStatus}`;
        if (disabledButtons.has(key)) return;
        setDisabledButtons((values) => new Set(values).add(key));
        mutate({ uri, newStatus});
    }

    useEffect(() => {
        if (!isFetching) setDisabledButtons(new Set());
    }, [isFetching]);

    return <Group gap={2} wrap="nowrap">
        {(Object.entries(transitions) as [SyncStatus, string][]).map(
            ([ toStatus, actionDesc ]) => {
                const info = statusDetails[toStatus];
                const key = `${node.uri}:${toStatus}`;
                return <Tooltip key={key} label={actionDesc}>
                    <ActionIcon
                        size="sm"
                        variant="light"
                        color={info.color}
                        disabled={disabledButtons.has(key)}
                        onClick={(event) => {
                            event.stopPropagation();
                            buttonClick(node.uri, toStatus);
                        }}
                    >
                        <info.icon size={16} />
                    </ActionIcon>
                </Tooltip>
            }
        )}
    </Group>
}
