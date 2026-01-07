import axios from "axios";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_FETCH_AUTH_URL || "http://95.216.121.250:800";

export const axiosBase = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});
