import client from "./client";

export interface User {
    id: string;
    email: string;
    full_name: string | null;
    is_superuser: boolean;
}

export interface LoginData {
    username: string;
    password: string;
}

export interface RegisterData {
    email: string;
    password: string;
    full_name: string;
}

export async function getCurrentUser(): Promise<User | null> {
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
