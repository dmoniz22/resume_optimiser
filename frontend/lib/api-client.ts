const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export class ApiClient {
  private baseUrl: string;
  private getToken: () => Promise<string | null>;

  constructor(getToken: () => Promise<string | null>) {
    this.baseUrl = API_URL;
    this.getToken = getToken;
  }

  private async headers(): Promise<HeadersInit> {
    const token = await this.getToken();
    const headers: HeadersInit = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return headers;
  }

  async get(path: string) {
    const res = await fetch(`${this.baseUrl}${path}`, { headers: await this.headers() });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async post(path: string, body?: unknown) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: await this.headers(),
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async put(path: string, body?: unknown) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "PUT",
      headers: await this.headers(),
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async delete(path: string) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "DELETE",
      headers: await this.headers(),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
}
