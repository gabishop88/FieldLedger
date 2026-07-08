import { ActionIcon, Group, ScrollArea, Stack, Text, Title, Tooltip } from "@mantine/core";
import { IconArrowDown, IconTrashFilled } from "@tabler/icons-react";
import { useEffect, useRef, useState } from "react";
import { useWorkerLogs } from "../hooks/use_worker_logs";

export default function LogViewer() {
    const { logs, setLogs } = useWorkerLogs();

    const viewport = useRef<HTMLDivElement>(null);
    const [atBottom, setAtBottom] = useState(true);

    const scrollToBottom = () => viewport.current?.scrollTo(
        { top: viewport.current.scrollHeight, behavior: "smooth" }
    );

    useEffect(() => { if (atBottom) scrollToBottom(); }, [logs, atBottom]);

    return <Stack h="100%" p="xs">
        <Group align="flex-end">
            <Tooltip label="Scroll to End">
                <ActionIcon onClick={scrollToBottom} variant="subtle" disabled={atBottom}>
                    <IconArrowDown size={16} />
                </ActionIcon>
            </Tooltip>

            <Tooltip label="Clear Logs">
                <ActionIcon color="red" onClick={() => setLogs([])} variant="subtle">
                    <IconTrashFilled size={16} />
                </ActionIcon>
            </Tooltip>

            <Text size="md">Worker Logs</Text>
        </Group>

        <ScrollArea
            viewportRef={viewport}
            onBottomReached={() => setAtBottom(true)}
            onScrollPositionChange={({ y }) => {
                const vp = viewport.current;
                if (!vp) return;
                if (vp.scrollHeight - y - vp.clientHeight > 10) setAtBottom(false);
            }}
        >
            {logs.map((log, i) => 
                <Text key={i} ff="monospace" fz="xs">
                    {log}
                </Text>
            )}
        </ScrollArea>
    </Stack>
}
