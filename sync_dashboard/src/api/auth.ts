import type { LoginData, RegisterData, User } from "../types/fl";
import client from "./client";

export async function currentUserRequest(): Promise<User | null> {
    try {
        const { data } = await client.get<User>("/account");
        return data;
    } catch {
        return null;
    }
}

export async function loginRequest(form: LoginData): Promise<User> {
    const { data } = await client.post<User>("/account/login/access-cookie", form);
    return data;
}

export async function createAccountRequest(form: RegisterData): Promise<User> {
    const { data } = await client.post<User>("/account", form);
    return data;
}

export async function deleteAccountRequest(): Promise<User> {
    const { data } = await client.delete<User>("/account");
    return data;
}


export async function logoutRequest(): Promise<void> {
    await client.post("/account/logout");
}
