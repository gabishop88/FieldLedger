import { createContext, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";

import {
    type LoginData,
    type User,
    getCurrentUser,
    loginRequest,
    logoutRequest 
} from "../api/auth";

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login(data: LoginData): Promise<void>;
    logout(): Promise<void>;
    refresh(): Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export default function AuthProvider({ children }: { children: ReactNode }) {
    const queryClient = useQueryClient();
    const query = useQuery({
        queryKey: ["currentUser"],
        queryFn: getCurrentUser,
    });

    async function refresh() {
        await queryClient.refetchQueries({ queryKey: ["currentUser"] })
    }

    async function login(data: LoginData) {
        try{
            await loginRequest(data);
            await refresh();
            notifications.show({title: "Logged In", message: "Authentication successful."});
        } catch {
            notifications.show({color: "red", title: "Login Failed", message: "Invalid email or password."});
            throw Error("Login failed.");
        }
    }

    async function logout() {
        await logoutRequest();
        await refresh();
        notifications.show({title: "Logged Out", message: "Authentication cookie removed."});
    }

    return (
        <AuthContext.Provider
            value={{
                user: query.data ?? null,
                loading: query.isLoading,
                login,
                logout,
                refresh,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}
