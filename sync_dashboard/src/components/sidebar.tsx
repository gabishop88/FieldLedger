import { Stack } from "@mantine/core";

import JDAuthButtonGroup from "./jd_connect_button";
import SyncTree from "./sync_tree";
import { type JDAuthInfo, type SyncTreeNode } from "../api/jd";

interface Props {
    loggedIn: boolean;
    jdAuth: JDAuthInfo | null;
    trees: SyncTreeNode[];

    selectedField: SyncTreeNode | null;
    onSelectField: (field: SyncTreeNode | null) => void;
}

export default function SyncTreeSidebar({ 
    loggedIn, jdAuth, trees, selectedField, onSelectField
}: Props) {
    return (
        <Stack h="100%" p="md" gap="md">
            <JDAuthButtonGroup loggedIn={loggedIn} jdAuth={jdAuth} />

            <SyncTree 
                trees={trees}
                selectedField={selectedField}
                onSelectField={onSelectField}
            />
        </Stack>
    );
}
