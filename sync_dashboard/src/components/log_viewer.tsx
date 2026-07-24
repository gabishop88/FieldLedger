import { ActionIcon, Code, Group, ScrollArea, Stack, Text, Tooltip } from "@mantine/core";
import { IconChevronDown, IconCircleChevronsDown, IconTrash } from "@tabler/icons-react";
import { useEffect, useRef, useState } from "react";
import { useWorkerLogs } from "../hooks/use_worker_logs";

interface Props {
  toggleCollapse?: () => void;
}

export default function LogViewer({ toggleCollapse }: Props) {
  const { logs, setLogs } = useWorkerLogs(100);

  const viewport = useRef<HTMLDivElement>(null);
  const [atBottom, setAtBottom] = useState(true);

  const scrollToBottom = () => viewport.current?.scrollTo(
    { top: viewport.current.scrollHeight, behavior: "smooth" }
  );

  useEffect(() => { if (atBottom) scrollToBottom(); }, [logs, atBottom]);

  return <Stack h="100%" w="100%">
    <Group align="baseline" gap="xs">
      <Tooltip label="Collapse Log Panel">
        <ActionIcon onClick={toggleCollapse} variant="subtle" color="gray">
          <IconChevronDown size={18} />
        </ActionIcon>
      </Tooltip>

      <Tooltip label="Scroll to End">
        <ActionIcon onClick={scrollToBottom} variant="subtle" disabled={atBottom}>
          <IconCircleChevronsDown size={18} />
        </ActionIcon>
      </Tooltip>

      <Tooltip label="Clear Logs">
        <ActionIcon color="red" onClick={() => setLogs([])} variant="subtle">
          <IconTrash size={18} />
        </ActionIcon>
      </Tooltip>

      <Text size="md">Worker Logs</Text>
    </Group>

    <ScrollArea
      w="100%"
      viewportRef={viewport}
      onBottomReached={() => setAtBottom(true)}
      onScrollPositionChange={({ y }) => {
        const vp = viewport.current;
        if (!vp) return;
        if (vp.scrollHeight - y - vp.clientHeight > 10) setAtBottom(false);
      }}
    >
      <Code block p="sm" w="100%">
        {logs.map((log, i) => 
          <Text w="100%" pt="xs" textWrap="wrap" key={i} ff="monospace" fz="sm">{log}</Text>
        )}
      </Code>
    </ScrollArea>
  </Stack>
}
