import { API_URL } from "./constants";

const credentials = API_URL.includes("localhost") ? "include" : "same-origin";

console.log(credentials);
const commonHeaders = {
  "Content-Type": "application/json",
};

function initWithDefaults(
  method: "GET" | "POST",
  init?: RequestInit,
): RequestInit {
  return {
    credentials,
    ...init,
    headers: {
      ...commonHeaders,
      ...init?.headers,
    },
    method: method,
  };
}

export function get(url: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_URL}${url}`, initWithDefaults("GET", init));
}

export function post(url: string, init?: RequestInit) {
  return fetch(`${API_URL}${url}`, initWithDefaults("POST", init));
}
