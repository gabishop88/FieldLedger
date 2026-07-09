import { createContext, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";

import {
    currentUserRequest,
    loginRequest,
    createAccountRequest,
    logoutRequest,
    deleteAccountRequest,
} from "../api/auth";
import type { LoginData, RegisterData, User } from "../types/fl";

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login(data: LoginData): Promise<void>;
    register(data: RegisterData): Promise<void>;
    deleteAccount(): Promise<void>;
    logout(): Promise<void>;
    refresh(): Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export default function AuthProvider({ children }: { children: ReactNode }) {
    const queryClient = useQueryClient();
    const query = useQuery({
        queryKey: ["currentUser"],
        queryFn: currentUserRequest,
    });

    async function refresh() {
        await queryClient.refetchQueries({ queryKey: ["currentUser"] })
        await queryClient.refetchQueries({ queryKey: ["jd"] })
    }

    async function login(data: LoginData) {
        try {
            await loginRequest(data);
            await refresh();
            notifications.show({ title: "Logged In", message: "Authentication successful." });
        } catch {
            notifications.show({ color: "red", title: "Login Failed", message: "Invalid email or password." });
            throw Error("Login failed.");
        }
    }

    async function register(data: RegisterData) {
        try {
            await createAccountRequest(data);
            await loginRequest({ username: data.email, password: data.password })
            await refresh();
            notifications.show({ title: "Account Created", message: "Successfully logged in." });
        } catch {
            notifications.show({ color: "red", title: "Registration Failed", message: "Unable to create account." });
            throw Error("Register failed.");
        }
    }

    async function deleteAccount() {
        try {
            await deleteAccountRequest();
            await logoutRequest(); // logging out afterwards in case deletion failed. logout just removes cookie anyway.
            await refresh();
            notifications.show({ title: "Account Deleted", message: "Your account has been deleted permanently." });
        } catch {
            notifications.show({ color: "red", title: "Deletion Failed", message: "Unable to delete the account." });
            throw Error("Account deletion failed.")
        }
    }

    async function logout() {
        await logoutRequest();
        await refresh();
        notifications.show({ title: "Logged Out", message: "Authentication cookie removed." });
    }

    return (
        <AuthContext.Provider
            value={{
                user: query.data ?? null,
                loading: query.isLoading,
                login,
                register,
                deleteAccount,
                logout,
                refresh,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}
