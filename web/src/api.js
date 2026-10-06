export async function api(path, options = {}) {
  const headers = { ...options.headers }
  if (options.body !== undefined && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    headers,
    body: options.body === undefined || options.body instanceof FormData
      ? options.body : JSON.stringify(options.body),
  })
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const data = await response.json()
      detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    } catch { /* The response was not JSON. */ }
    throw new Error(detail)
  }
  return response.status === 204 ? null : response.json()
}

export const projectApi = {
  directory: () => api('/project-directory'),
  create: body => api('/projects', { method: 'POST', body }),
  update: (id, body) => api(`/projects/${id}`, { method: 'PUT', body }),
  move: (id, body) => api(`/projects/${id}/move`, { method: 'PUT', body }),
  archive: id => api(`/projects/${id}/archive`, { method: 'POST' }),
  remove: id => api(`/projects/${id}`, { method: 'DELETE' }),
  category: name => api('/project-categories', { method: 'POST', body: { name } }),
  renameCategory: (id, name) => api(`/project-categories/${id}`, { method: 'PUT', body: { name } }),
  removeCategory: id => api(`/project-categories/${id}`, { method: 'DELETE' }),
}
