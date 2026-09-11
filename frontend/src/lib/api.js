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

// ---------------------------------------------------------------------------
// Complaints API
// ---------------------------------------------------------------------------

export async function createComplaint(formData) {
  const response = await fetch(`${API_BASE}/complaints`, {
    method: "POST",
    credentials: "include",
    body: formData,
  })
  return handleResponse(response)
}

export async function getComplaints({ category, status, mine, mine_only, page = 1, page_size = 50, limit, offset } = {}) {
  const query = new URLSearchParams()
  if (category && category !== "ALL") query.set("category", category)
  if (status && status !== "ALL") query.set("status", status)
  const isMine = mine !== undefined ? mine : mine_only
  if (isMine !== undefined) query.set("mine", String(isMine))
  if (limit) query.set("limit", String(limit))
  else if (page_size) query.set("limit", String(page_size))
  if (offset !== undefined) query.set("offset", String(offset))
  else if (page && page_size) query.set("offset", String((page - 1) * page_size))

  const queryString = query.toString()
  const url = `${API_BASE}/complaints${queryString ? `?${queryString}` : ""}`
  const response = await fetch(url, {
    method: "GET",
    credentials: "include",
  })
  const data = await handleResponse(response)
  if (Array.isArray(data)) {
    return {
      items: data,
      total: data.length,
    }
  }
  return data || { items: [], total: 0 }
}

export async function getComplaint(id) {
  const response = await fetch(`${API_BASE}/complaints/${id}`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function getCitizenDashboardStats() {
  const response = await fetch(`${API_BASE}/complaints/stats/citizen`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function upvoteComplaint(id) {
  const response = await fetch(`${API_BASE}/complaints/${id}/upvote`, {
    method: "POST",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function removeUpvoteComplaint(id) {
  const response = await fetch(`${API_BASE}/complaints/${id}/upvote`, {
    method: "DELETE",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function getComplaintUpvoteStatus(id) {
  const response = await fetch(`${API_BASE}/complaints/${id}/upvote`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}

// ---------------------------------------------------------------------------
// Admin API
// ---------------------------------------------------------------------------

export async function getAdminDashboardStats(cityId = null) {
  const query = new URLSearchParams()
  if (cityId) query.set("city_id", cityId)
  const qs = query.toString()
  const response = await fetch(`${API_BASE}/admin/dashboard${qs ? `?${qs}` : ""}`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function getAdminComplaints({
  search,
  status,
  severity,
  category,
  department_id,
  city_id,
  min_priority,
  limit = 50,
  offset = 0,
} = {}) {
  const query = new URLSearchParams()
  if (search) query.set("search", search)
  if (status && status !== "ALL") query.set("status", status)
  if (severity && severity !== "ALL") query.set("severity", severity)
  if (category && category !== "ALL") query.set("category", category)
  if (department_id && department_id !== "ALL") query.set("department_id", department_id)
  if (city_id) query.set("city_id", city_id)
  if (min_priority !== undefined && min_priority !== null && min_priority !== "") {
    query.set("min_priority", String(min_priority))
  }
  query.set("limit", String(limit))
  query.set("offset", String(offset))

  const qs = query.toString()
  const response = await fetch(`${API_BASE}/admin/complaints${qs ? `?${qs}` : ""}`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function getAdminComplaint(id) {
  const response = await fetch(`${API_BASE}/admin/complaints/${id}`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}

export async function updateAdminComplaintSeverity(id, { severity, remark }) {
  const response = await fetch(`${API_BASE}/admin/complaints/${id}/severity`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ severity, remark }),
  })
  return handleResponse(response)
}

export async function assignAdminComplaintDepartment(id, { department_id, remark }) {
  const response = await fetch(`${API_BASE}/admin/complaints/${id}/department`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ department_id, remark }),
  })
  return handleResponse(response)
}

export async function transitionAdminComplaintStatus(id, { status, remark, department_id }) {
  const response = await fetch(`${API_BASE}/admin/complaints/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ status, remark, department_id }),
  })
  return handleResponse(response)
}

export async function addAdminComplaintRemark(id, { remark }) {
  const response = await fetch(`${API_BASE}/admin/complaints/${id}/remarks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ remark }),
  })
  return handleResponse(response)
}

export async function getAdminDepartments(cityId = null) {
  const query = new URLSearchParams()
  if (cityId) query.set("city_id", cityId)
  const qs = query.toString()
  const response = await fetch(`${API_BASE}/admin/departments${qs ? `?${qs}` : ""}`, {
    method: "GET",
    credentials: "include",
  })
  return handleResponse(response)
}

