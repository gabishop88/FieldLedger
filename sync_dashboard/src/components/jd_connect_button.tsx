import { Button, Group, Tooltip } from "@mantine/core";
import type { JDAuthInfo } from "../api/jd";
import { IconTrash } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useDeleteJDAuth } from "../hooks/use_jd_auth";
import ConfirmationModal from "./confirm_modal";

interface Props {
    loggedIn: boolean;
    jdAuth: JDAuthInfo | null;
}

export default function JDAuthButtonGroup({ loggedIn, jdAuth }: Props) {
    const queryClient = useQueryClient();
    useEffect(() => {
        queryClient.invalidateQueries({ queryKey: ["jd", "syncTree"] });
    }, [jdAuth?.authorized, queryClient]);

    const [confirmOpen, setConfirmOpen] = useState(false);
    const { mutate, isPending } = useDeleteJDAuth();

    return <Group w="100%" justify="space-between" gap={4}>
            <Tooltip label="Log into FieldLedger first." hidden={loggedIn}>
                <Button 
                    mih="20px"
                    flex={7}
                    component="a"
                    href={jdAuth?.auth_uri ?? ""}
                    data-disabled={!loggedIn || (jdAuth?.authorized ?? true)}
                    onClick={(event) => {
                        if (jdAuth?.authorized ?? false) event.preventDefault();
                    }}
                    target="_self"
                    rel="noopener noreferrer"
                >
                    {jdAuth?.authorized ? "John Deere Connected" : "Connect John Deere"}
                </Button>
            </Tooltip>
            
            {loggedIn && jdAuth?.authorized && <>
                <ConfirmationModal 
                    opened={confirmOpen} 
                    onClose={() => setConfirmOpen(false)}
                    onConfirm={mutate}
                    loading={isPending}
                    title="Clear sync data?"
                    buttonLabel="Delete Connection"
                >
                    This will delete your connection, synced links, and data created during sync.
                </ConfirmationModal>

                <Button
                    color="red"
                    variant="subtle"
                    flex={1}
                    onClick={() => setConfirmOpen(true)}
                >
                    <IconTrash size={18} />
                </Button>
            </>}
    </Group>
}
