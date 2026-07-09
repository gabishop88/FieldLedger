import { Button, Divider, Group, Stack, Tooltip, Text } from "@mantine/core";

import JDAuthButtons from "../auth/jd_auth_buttons"
import SyncTree from "./sync_tree";
import type { JDAuthInfo, JDField, JDOrg } from "../../types/jd";
import type { SyncLink } from "../../types/fl";
import { useSyncTree } from "../../hooks/use_sync_tree";
import { IconClick, IconListTree, IconRefresh } from "@tabler/icons-react";
import SyncStatusHelp from "./status_info";

interface Props {
    loggedIn: boolean;
    jdAuth: JDAuthInfo | null;
    trees: SyncLink<JDOrg>[];

    selectedField: SyncLink<JDField> | null;
    onSelectField: (field: SyncLink<JDField> | null) => void;
}

export default function SyncExplorerPanel({ 
    loggedIn, jdAuth, trees, selectedField, onSelectField
}: Props) {
    const { refetch, isFetching } = useSyncTree(true);
    return <Stack h="100%">
        <JDAuthButtons loggedIn={loggedIn} jdAuth={jdAuth} />

        <Divider />

        <Group wrap="wrap" justify="space-around">
            <Group justify="center">
                <IconListTree size={16} />
                <Text size="xs">Organizations</Text>
                <IconClick size={16} />
                <Text size="xs">Farms</Text>
                <IconClick size={16} />
                <Text size="xs">Fields</Text>
            </Group>

            <Group justify="space-between">
                <Tooltip label="Refresh">
                    <Button 
                        size="xs"
                        variant="outline"
                        onClick={async () => await refetch()}
                        loading={isFetching}
                    >
                        <IconRefresh size={16} />
                    </Button>
                </Tooltip>

                <SyncStatusHelp />
            </Group>
        </Group>

        <Divider />

        <SyncTree 
            trees={trees}
            selectedField={selectedField}
            onSelectField={onSelectField}
        />
    </Stack>
}
