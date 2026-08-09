/** Thin fetch wrapper against the Commerce Engine API. */

export type ApiClientOptions = {
  baseUrl?: string;
  tenantId?: string;
  getAccessToken?: () => string | null | Promise<string | null>;
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function createApiClient(options: ApiClientOptions = {}) {
  const baseUrl = options.baseUrl ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (options.tenantId) {
      headers.set("X-Tenant-ID", options.tenantId);
    }
    const token = options.getAccessToken ? await options.getAccessToken() : null;
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${baseUrl}${path}`, { ...init, headers });
    if (!response.ok) {
      let code = "HTTP_ERROR";
      let message = response.statusText;
      try {
        const body = (await response.json()) as {
          error?: { code?: string; message?: string };
        };
        code = body.error?.code ?? code;
        message = body.error?.message ?? message;
      } catch {
        // ignore JSON parse errors
      }
      throw new ApiError(response.status, code, message);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  }

  return {
    getHealth: () => request<{ status: string }>("/health"),
    getMeta: () =>
      request<{ name: string; version: string; environment: string }>("/api/v1/meta"),
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
