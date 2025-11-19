import axios from "axios";

const API = "http://127.0.0.1:8000";

// === Pipeline Management ===
export const runPipeline = async (config) => {
  const response = await axios.post(`${API}/pipeline/run`, config);
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await axios.get(`${API}/pipeline/status/${jobId}`);
  return response.data;
};

export const listJobs = async () => {
  const response = await axios.get(`${API}/pipeline/jobs`);
  return response.data;
};

// === Subreddit Data ===
export const listSubreddits = async () => {
  const response = await axios.get(`${API}/subreddits`);
  return response.data;
};

export const getSubredditHistory = async (subreddit) => {
  const response = await axios.get(`${API}/data/${subreddit}/history`);
  return response.data;
};

export const getSubredditData = async (subreddit) => {
  const response = await axios.get(`${API}/data/${subreddit}`);
  return response.data;
};

export const fetchMetadata = async (subreddit) => {
  const response = await axios.get(`${API}/data/${subreddit}/metadata`);
  return response.data;
};

export const fetchCategories = async (subreddit) => {
  const response = await axios.get(`${API}/data/${subreddit}/categories`);
  return response.data;
};

export const fetchInsights = async (subreddit) => {
  const response = await axios.get(`${API}/data/${subreddit}/insights`);
  return response.data;
};

export const fetchInsight = async (subreddit, id) => {
  const response = await axios.get(`${API}/data/${subreddit}/insights/${id}`);
  return response.data;
};

// === Health Check ===
export const healthCheck = async () => {
  const response = await axios.get(`${API}/health`);
  return response.data;
};
