import { Divider, Stack } from "@mantine/core";

import JDConnectButton from "./jd_connect_button";
import SyncTree from "./sync_tree";
import { type JDAuthInfo, type SyncTreeNode } from "../api/jd";

interface Props {
    loggedIn: boolean;
    jdAuth: JDAuthInfo | null;
    trees: SyncTreeNode[];
}

export default function SyncTreeSidebar({ loggedIn, jdAuth, trees }: Props) {
    return (
        <Stack h="100%" p="md">
            <JDConnectButton loggedIn={loggedIn} jdAuth={jdAuth} />

            <Divider />

            <SyncTree trees={trees} />
        </Stack>
    );
}
