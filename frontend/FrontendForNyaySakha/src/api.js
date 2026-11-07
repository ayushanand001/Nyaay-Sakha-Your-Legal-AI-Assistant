export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

export async function api(path, { method = 'GET', token, json, formData } = {}) {
  const headers = {}

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  let body

  if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  } else if (formData) {
    body = formData
  }

  let response

  try {
    response = await fetch(path, { method, headers, body })
  } catch {
    throw new ApiError(0, 'The Nyay Sakha API is not reachable.')
  }

  const text = await response.text()
  let data = null

  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, messageFrom(data))
  }

  return data
}

export async function downloadFile(path, token, filename) {
  let response

  try {
    response = await fetch(path, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new ApiError(0, 'The Nyay Sakha API is not reachable.')
  }

  if (!response.ok) {
    const text = await response.text()
    let data
    try {
      data = text ? JSON.parse(text) : null
    } catch {
      data = { detail: text }
    }
    throw new ApiError(response.status, messageFrom(data))
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function messageFrom(data) {
  if (!data) return 'The request could not be completed.'
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => item.msg || 'Check the form and try again.')
      .join(' ')
  }
  return 'The request could not be completed.'
}
