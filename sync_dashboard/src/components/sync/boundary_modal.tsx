import type { SyncLink } from "../../types/fl";
import { Badge, Group, Modal, Stack, Text } from "@mantine/core";
import { statusDetails, SyncActions, SyncIcon } from "./status_info";
import { BoundaryCard } from "./op_details";

interface Props {
  boundary: SyncLink<"boundary"> | null;
  onClose: () => void;
}

export default function BoundaryModal({ boundary, onClose }: Props) {
  const status = boundary?.status || "Unsynced";
  return !boundary
    ? <Modal opened={false} onClose={onClose} />
    : <Modal opened onClose={onClose} title="Boundary Sync" size="lg">
        <Stack gap="md">
          <BoundaryCard link={boundary} mapH={300}/>

          <Group justify="space-between" px="lg">
            <Badge
              variant="light"
              size="lg"
              color={statusDetails[status].color}
              leftSection={<SyncIcon status={status} />}
            >
              {boundary.status}
            </Badge>

            <Group align="flex-start">
              <Text>Actions:</Text>
              <SyncActions node={boundary} />
            </Group>
          </Group>
        </Stack>
      </Modal>;
}
