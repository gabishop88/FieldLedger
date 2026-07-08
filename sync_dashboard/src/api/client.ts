import axios from "axios";

export const API_PREFIX = "/api/v1"

const client = axios.create({
    baseURL: API_PREFIX,
    withCredentials: true,
});

export default client;
