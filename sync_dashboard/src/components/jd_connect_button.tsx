import { Button, Tooltip } from "@mantine/core";
import type { JDAuthInfo } from "../api/jd";

interface Props {
    loggedIn: boolean;
    jdAuth: JDAuthInfo | null;
}

export default function JDConnectButton({ loggedIn, jdAuth }: Props) {
    return !loggedIn ? (
        <Tooltip label="Log into FieldLedger first.">
            <Button fullWidth disabled>Connect John Deere</Button>
        </Tooltip>
    ) : (
        <Button 
            fullWidth
            component="a"
            href={jdAuth?.auth_uri}
            disabled={jdAuth?.authorized ?? true}
            rel="noopener noreferrer"
        >
            {jdAuth?.authorized ? "John Deere Connected" : "Connect John Deere"}
        </Button>
    )
}
