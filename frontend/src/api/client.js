import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
let tokenProvider = async () => null;

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

export const setAuthTokenProvider = (providerFn) => {
  tokenProvider = providerFn || (async () => null);
};

api.interceptors.request.use(async (config) => {
  const token = await tokenProvider();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const startGithubScan = async (payload) => {
  const { data } = await api.post("/scan/github", payload);
  return data;
};

export const startUploadScan = async (formData) => {
  const { data } = await api.post("/scan/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const getScanStatus = async (scanId) => {
  const { data } = await api.get("/scan/status", { params: { scan_id: scanId } });
  return data;
};

export const getScanHistory = async (limit = 25) => {
  const { data } = await api.get("/scan/history", { params: { limit } });
  return data.items || [];
};

export const getAnalytics = async () => {
  const { data } = await api.get("/scan/analytics");
  return data;
};

export const compareScans = async (scanIdA, scanIdB) => {
  const { data } = await api.get("/scan/compare", {
    params: { scan_id_a: scanIdA, scan_id_b: scanIdB },
  });
  return data;
};

export const exportScanJson = async (scanId) => {
  const { data } = await api.get(`/scan/export/${scanId}`);
  return data;
};

export const generateReport = async (scanId, reportType = "pdf") => {
  if (reportType === "json") {
    const { data } = await api.post("/generate/report", {
      scan_id: scanId,
      report_type: "json",
    });
    return data;
  }
  const response = await api.post(
    "/generate/report",
    { scan_id: scanId, report_type: "pdf" },
    { responseType: "blob" }
  );
  return response.data;
};

export const getAuthProfile = async () => {
  const { data } = await api.get("/auth/me");
  return data;
};
