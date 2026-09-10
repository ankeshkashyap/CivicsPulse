import React, { createContext, useContext } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getCurrentUser, requestOtp, verifyOtp, logoutUser } from "@/lib/api"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const queryClient = useQueryClient()

  // Load current user profile from HttpOnly session
  const {
    data: user,
    isLoading,
    isError,
    refetch: refetchUser,
  } = useQuery({
    queryKey: ["currentUser"],
    queryFn: getCurrentUser,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  // Request OTP mutation
  const requestOtpMutation = useMutation({
    mutationFn: (email) => requestOtp(email),
  })

  // Verify OTP mutation
  const verifyOtpMutation = useMutation({
    mutationFn: ({ email, otp }) => verifyOtp(email, otp),
    onSuccess: (data) => {
      // Invalidate and immediately set current user data in cache
      if (data?.user) {
        queryClient.setQueryData(["currentUser"], data.user)
      } else {
        queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      }
    },
  })

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: logoutUser,
    onSuccess: () => {
      queryClient.setQueryData(["currentUser"], null)
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
    },
  })

  const value = {
    user: isError ? null : user,
    isLoading,
    isAuthenticated: Boolean(user && !isError),
    requestOtp: requestOtpMutation.mutateAsync,
    isRequestingOtp: requestOtpMutation.isPending,
    verifyOtp: verifyOtpMutation.mutateAsync,
    isVerifyingOtp: verifyOtpMutation.isPending,
    logout: logoutMutation.mutateAsync,
    isLoggingOut: logoutMutation.isPending,
    refetchUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
