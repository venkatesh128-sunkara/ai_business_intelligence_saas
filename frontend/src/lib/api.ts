import axios from "axios";
import type {
  AdminStats,
  Dashboard,
  Dataset,
  Insight,
  QueryHistory,
  QueryResult,
  Usage,
  User,
  Workspace,
} from "./types";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

function errMsg(e: unknown): string {
  const err = e as { response?: { data?: { detail?: string } }; message?: string };
  return err.response?.data?.detail ?? err.message ?? "Request failed";
}

export const authApi = {
  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const body = new URLSearchParams({ username: email, password });
    const { data } = await api.post("/auth/login", body, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return data;
  },
  async register(name: string, email: string, password: string): Promise<{ access_token: string; user: User }> {
    const { data } = await api.post("/auth/register", { name, email, password });
    return data;
  },
};

export const workspacesApi = {
  async list(): Promise<Workspace[]> {
    const { data } = await api.get("/workspaces");
    return data;
  },
  async create(name: string, description: string): Promise<Workspace> {
    const { data } = await api.post("/workspaces", { name, description });
    return data;
  },
  async usage(workspaceId: number): Promise<Usage> {
    const { data } = await api.get(`/workspaces/${workspaceId}/usage`);
    return data;
  },
};

export const datasetsApi = {
  async list(): Promise<{ items: Dataset[]; total: number }> {
    const { data } = await api.get("/datasets");
    return data;
  },
  async get(id: number): Promise<Dataset> {
    const { data } = await api.get(`/datasets/${id}`);
    return data;
  },
  async preview(id: number, limit = 50): Promise<{ columns: string[]; rows: unknown[][] }> {
    const { data } = await api.get(`/datasets/${id}/preview`, { params: { limit } });
    return data;
  },
  async upload(workspaceId: number, name: string, file: File): Promise<Dataset> {
    const fd = new FormData();
    fd.append("workspace_id", String(workspaceId));
    fd.append("name", name);
    fd.append("file", file);
    const { data } = await api.post("/datasets", fd);
    return data;
  },
  async remove(id: number): Promise<void> {
    await api.delete(`/datasets/${id}`);
  },
};

export const queryApi = {
  async ask(question: string, datasetId: number, conversationId?: string): Promise<QueryResult> {
    const { data } = await api.post("/query/ask", { question, dataset_id: datasetId, conversation_id: conversationId });
    return data;
  },
  async history(datasetId?: number): Promise<QueryHistory> {
    const { data } = await api.get("/query/history", { params: datasetId ? { dataset_id: datasetId } : {} });
    return data;
  },
  async remove(id: number): Promise<void> {
    await api.delete(`/query/${id}`);
  },
};

export const insightsApi = {
  async generate(datasetId: number, useLlm = true): Promise<Insight[]> {
    const { data } = await api.post(`/insights/generate?dataset_id=${datasetId}&use_llm=${useLlm}`);
    return data.insights;
  },
};

export const dashboardsApi = {
  async list(): Promise<Dashboard[]> {
    const { data } = await api.get("/dashboards");
    return data;
  },
  async create(workspaceId: number, name: string, description: string): Promise<Dashboard> {
    const { data } = await api.post(`/dashboards?workspace_id=${workspaceId}`, { name, description });
    return data;
  },
  async get(id: number): Promise<Dashboard> {
    const { data } = await api.get(`/dashboards/${id}`);
    return data;
  },
  async addItem(dashboardId: number, queryId: number, title: string): Promise<unknown> {
    const { data } = await api.post(`/dashboards/${dashboardId}/items`, { query_id: queryId, title });
    return data;
  },
  async removeItem(itemId: number): Promise<void> {
    await api.delete(`/dashboards/items/${itemId}`);
  },
  async remove(dashboardId: number): Promise<void> {
    await api.delete(`/dashboards/${dashboardId}`);
  },
};

export const adminApi = {
  async stats(): Promise<AdminStats> {
    const { data } = await api.get("/admin/stats");
    return data;
  },
};

export { errMsg };
