const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const ASSET_BASE_URL = import.meta.env.VITE_ASSET_BASE_URL || ''

const ACCESS_TOKEN_KEY = 'agri-access-token'
const REFRESH_TOKEN_KEY = 'agri-refresh-token'
const USER_KEY = 'agri-current-user'

export const tokenStore = {
  getAccessToken() {
    return window.localStorage.getItem(ACCESS_TOKEN_KEY)
  },
  getRefreshToken() {
    return window.localStorage.getItem(REFRESH_TOKEN_KEY)
  },
  getUser() {
    const raw = window.localStorage.getItem(USER_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw)
    } catch {
      return null
    }
  },
  setSession({ accessToken, refreshToken, user }) {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    window.localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  setUser(user) {
    window.localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  clear() {
    window.localStorage.removeItem(ACCESS_TOKEN_KEY)
    window.localStorage.removeItem(REFRESH_TOKEN_KEY)
    window.localStorage.removeItem(USER_KEY)
  }
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const isFormData = options.body instanceof FormData
  if (!isFormData && options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const accessToken = tokenStore.getAccessToken()
  if (accessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body: isFormData || typeof options.body === 'string' ? options.body : options.body ? JSON.stringify(options.body) : undefined
  })

  const text = await response.text()
  const payload = text ? JSON.parse(text) : null
  if (!response.ok || payload?.success === false) {
    if (response.status === 401) {
      tokenStore.clear()
      window.dispatchEvent(new CustomEvent('agri-auth-expired'))
    }
    throw new Error(payload?.message || `请求失败：${response.status}`)
  }
  return payload?.data ?? payload
}

export const authApi = {
  register(body) {
    return apiRequest('/auth/register', { method: 'POST', body })
  },
  login(body) {
    return apiRequest('/auth/login', { method: 'POST', body })
  },
  sendCode(body) {
    return apiRequest('/auth/send-code', { method: 'POST', body })
  },
  forgotPassword(body) {
    return apiRequest('/auth/forgot-password', { method: 'POST', body })
  },
  resetPassword(body) {
    return apiRequest('/auth/reset-password', { method: 'POST', body })
  },
  logout(refreshToken) {
    return apiRequest('/auth/logout', { method: 'POST', body: { refreshToken } })
  },
  me() {
    return apiRequest('/auth/me')
  },
  changePassword(body) {
    return apiRequest('/auth/password', { method: 'PUT', body })
  }
}

export const dashboardApi = {
  overview: () => apiRequest('/dashboard/overview'),
  realtime: () => apiRequest('/dashboard/realtime'),
  trend: (params = {}) => apiRequest(withQuery('/dashboard/trend', params)),
  alerts: () => apiRequest('/dashboard/alerts')
}

export const taskApi = {
  list: (params = {}) => apiRequest(withQuery('/tasks', params)),
  create: (body) => apiRequest('/tasks', { method: 'POST', body }),
  update: (id, body) => apiRequest(`/tasks/${id}`, { method: 'PUT', body }),
  start: (id) => apiRequest(`/tasks/${id}/start`, { method: 'POST' }),
  stop: (id) => apiRequest(`/tasks/${id}/stop`, { method: 'POST' }),
  logs: (id) => apiRequest(`/tasks/${id}/logs`),
  status: (id) => apiRequest(`/tasks/${id}/status`)
}

export const analysisApi = {
  overview: () => apiRequest('/analysis/overview'),
  productStatistics: () => apiRequest('/analysis/product-statistics'),
  regionStatistics: () => apiRequest('/analysis/region-statistics'),
  dailyTrend: () => apiRequest('/analysis/daily-trend'),
  export: () => apiRequest('/analysis/export')
}

export const predictionApi = {
  list: () => apiRequest('/predictions'),
  detail: (product) => apiRequest(`/predictions/${encodeURIComponent(product)}`),
  factors: (product) => apiRequest(`/predictions/${encodeURIComponent(product)}/factors`),
  refresh: () => apiRequest('/predictions/refresh', { method: 'POST' })
}

export const alertApi = {
  rules: () => apiRequest('/alerts/rules'),
  records: (params = {}) => apiRequest(withQuery('/alerts/records', params)),
  ack: (id) => apiRequest(`/alerts/records/${id}/ack`, { method: 'PUT' }),
  close: (id) => apiRequest(`/alerts/records/${id}/close`, { method: 'PUT' })
}

export const userApi = {
  list: () => apiRequest('/users'),
  create: (body) => apiRequest('/users', { method: 'POST', body }),
  update: (id, body) => apiRequest(`/users/${id}`, { method: 'PUT', body }),
  remove: (id) => apiRequest(`/users/${id}`, { method: 'DELETE' }),
  changeRole: (id, role) => apiRequest(`/users/${id}/role`, { method: 'PUT', body: { role } }),
  changeStatus: (id, active) => apiRequest(`/users/${id}/status`, { method: 'PUT', body: { active } }),
  resetPassword: (id, password = 'Agri@123456') => apiRequest(`/users/${id}/reset-password`, { method: 'POST', body: { password } }),
  roles: () => apiRequest('/roles'),
  permissions: () => apiRequest('/permissions')
}

export const settingsApi = {
  get: () => apiRequest('/settings'),
  save: (body) => apiRequest('/settings', { method: 'PUT', body }),
  dbStatus: () => apiRequest('/settings/db-status'),
  auditLogs: () => apiRequest('/audit-logs')
}

export const profileApi = {
  get: () => apiRequest('/profile'),
  update: (body) => apiRequest('/profile', { method: 'PUT', body }),
  password: (body) => apiRequest('/profile/password', { method: 'POST', body }),
  preferences: (body) => apiRequest('/profile/preferences', { method: 'PUT', body }),
  avatar: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiRequest('/profile/avatar', { method: 'POST', body: formData })
  }
}

export function assetUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//.test(path) || path.startsWith('data:') || path.startsWith('blob:')) return path
  return `${ASSET_BASE_URL}${path}`
}

function withQuery(path, params) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value)
  })
  const query = search.toString()
  return query ? `${path}?${query}` : path
}