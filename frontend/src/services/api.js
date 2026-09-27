import axios from 'axios';

const hostDelFrontend = typeof window !== 'undefined' && window.location.hostname
  ? window.location.hostname
  : 'localhost';
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || `http://${hostDelFrontend}:8000`;

export const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, 
});