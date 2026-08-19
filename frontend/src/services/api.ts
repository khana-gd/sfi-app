export const getApiBaseUrl = () => {
  return import.meta.env.VITE_API_URL || "http://localhost:8000";
};

export const API_BASE_URL = `${getApiBaseUrl()}/api/v1`;

export const getWebSocketUrl = (ticket: string) => {
  const base = getApiBaseUrl();
  const wsBase = base.replace(/^http/, "ws");
  return `${wsBase}/api/v1/chat/ws?ticket=${ticket}`;
};

export interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  role: "STUDENT" | "FACULTY" | "ADMIN";
  is_active: boolean;
}

export interface Assignment {
  id: number;
  title: string;
  description: string;
  deadline: string;
  priority: string;
  category?: string;
  status: string;
  start_date: string;
  grading_criteria?: string;
  drive_file_id?: string;
  drive_file_name?: string;
  drive_file_url?: string;
}

export const api = {
  setToken(token: string) {
    localStorage.setItem("kanha_token", token);
  },

  getToken() {
    return localStorage.getItem("kanha_token");
  },

  logout() {
    localStorage.removeItem("kanha_token");
    localStorage.removeItem("kanha_user");
  },

  async request(endpoint: string, options: RequestInit = {}) {
    const token = this.getToken();
    const headers = {
      ...((options.headers as Record<string, string>) || {}),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Request failed");
    }

    return response.json();
  },

  async login(email: string, password: string): Promise<{ access_token: string; role: string }> {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const data = await this.request("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });

    this.setToken(data.access_token);
    return data;
  },

  async googleLogin(idToken: string): Promise<{ access_token: string; role: string }> {
    const data = await this.request("/auth/google", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ id_token: idToken }),
    });

    this.setToken(data.access_token);
    return data;
  },

  async googleMockLogin(emailOrName: string): Promise<{ access_token: string; role: string }> {
    const data = await this.request("/auth/google-mock", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ id_token: emailOrName }),
    });

    this.setToken(data.access_token);
    return data;
  },

  async getMe(): Promise<User> {
    const user = await this.request("/auth/me");
    localStorage.setItem("kanha_user", JSON.stringify(user));
    return user;
  },

  async getAssignments(): Promise<Assignment[]> {
    return this.request("/assignments");
  },

  async getAssignmentDetails(id: number): Promise<Assignment> {
    return this.request(`/assignments/${id}`);
  },

  async createAssignment(payload: any): Promise<Assignment> {
    return this.request("/assignments", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },

  async getUsers(): Promise<User[]> {
    return this.request("/users");
  },

  async createUser(payload: any): Promise<User> {
    return this.request("/users", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },

  async activateUser(userId: number): Promise<User> {
    return this.request(`/users/${userId}/activate`, {
      method: "PUT",
    });
  }
};
