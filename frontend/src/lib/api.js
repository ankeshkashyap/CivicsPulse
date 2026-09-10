/**
 * CivicPulse API client.
 * Dispatches requests with credentials: 'include' for HttpOnly cookie authentication.
 */

const API_BASE = "/api/v1"

async function handleResponse(response) {
  const contentType = response.headers.get("content-type") || ""
  const data = contentType.includes("application/json") ? await response.json() : null

  if (!response.ok) {
    const errorMsg = data?.message || data?.detail || `Request failed with status ${response.status}`
    const error = new Error(errorMsg)
    error.status = response.status
    error.data = data
    throw error
  }
  return data
}

export async function requestOtp(email) {
  const response = await fetch(`${API_BASE}/auth/request-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email }),
  })
  return handleResponse(response)
}

export async function verifyOtp(email, otp) {
  const response = await fetch(`${API_BASE}/auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, otp }),
  })
  return handleResponse(response)
}

export async function getCurrentUser() {
  const response = await fetch(`${API_BASE}/auth/me`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function logoutUser() {
  const response = await fetch(`${API_BASE}/auth/logout`, {
    method: "POST",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function testCitizenEndpoint() {
  const response = await fetch(`${API_BASE}/auth/test-citizen`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function testAdminEndpoint() {
  const response = await fetch(`${API_BASE}/auth/test-admin`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}
