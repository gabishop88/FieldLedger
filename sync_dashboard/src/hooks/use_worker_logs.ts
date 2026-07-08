import { useEffect, useState } from "react";
import { API_PREFIX } from "../api/client";

export function useWorkerLogs(limit=500) {
    const [ logs, setLogs ] = useState<string[]>([]);
    useEffect(() => {
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        const url = `${protocol}://${window.location.host}${API_PREFIX}/worker-logs?limit=${limit}`
        const socket = new WebSocket(url);

        socket.onmessage = (event: MessageEvent) => {
            setLogs((prev) => [...prev.slice(-(limit - 1)), event.data]);
        };
        return () => socket.close();
    }, [limit]);

    return { logs, setLogs };
}
