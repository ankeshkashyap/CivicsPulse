import React, { useState } from "react"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Mail, KeyRound, ArrowRight, RefreshCw, AlertCircle, CheckCircle2 } from "lucide-react"

export function LoginForm() {
  const { requestOtp, isRequestingOtp, verifyOtp, isVerifyingOtp } = useAuth()
  const [step, setStep] = useState("request") // 'request' | 'verify'
  const [email, setEmail] = useState("")
  const [otp, setOtp] = useState("")
  const [feedback, setFeedback] = useState({ type: null, text: "" })

  const handleRequestOtp = async (e) => {
    e.preventDefault()
    setFeedback({ type: null, text: "" })

    if (!email || !email.includes("@")) {
      setFeedback({ type: "error", text: "Please enter a valid email address." })
      return
    }

    try {
      const res = await requestOtp(email)
      setFeedback({
        type: "success",
        text: res.message || "If eligible, an OTP verification code has been dispatched.",
      })
      setStep("verify")
    } catch (err) {
      setFeedback({
        type: "error",
        text: err.message || "Failed to request verification code. Please try again.",
      })
    }
  }

  const handleVerifyOtp = async (e) => {
    e.preventDefault()
    setFeedback({ type: null, text: "" })

    if (!otp || otp.length !== 6) {
      setFeedback({ type: "error", text: "Please enter the 6-digit numeric verification code." })
      return
    }

    try {
      await verifyOtp({ email, otp })
      setFeedback({ type: "success", text: "Authentication successful! Welcome to CivicPulse." })
    } catch (err) {
      setFeedback({
        type: "error",
        text: err.message || "Invalid or expired verification code. Please verify and try again.",
      })
    }
  }

  return (
    <Card className="w-full max-w-md shadow-md border-border">
      <CardHeader className="text-center space-y-1">
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary mb-1">
          {step === "request" ? <Mail className="h-5 w-5" /> : <KeyRound className="h-5 w-5" />}
        </div>
        <CardTitle className="text-xl font-semibold tracking-tight">
          {step === "request" ? "Sign in to CivicPulse" : "Enter Verification Code"}
        </CardTitle>
        <CardDescription className="text-xs text-muted-foreground">
          {step === "request"
            ? "Passwordless authentication for Citizens and Municipal Officials"
            : `A 6-digit verification code was sent to ${email}`}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {feedback.text && (
          <div
            className={`flex items-start gap-2 p-3 rounded-md text-xs ${
              feedback.type === "error"
                ? "bg-destructive/10 text-destructive border border-destructive/20"
                : "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20"
            }`}
          >
            {feedback.type === "error" ? (
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            ) : (
              <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
            )}
            <span>{feedback.text}</span>
          </div>
        )}

        {step === "request" ? (
          <form onSubmit={handleRequestOtp} className="space-y-3">
            <div className="space-y-1">
              <label htmlFor="email" className="text-xs font-medium text-foreground">
                Email address
              </label>
              <Input
                id="email"
                type="email"
                placeholder="citizen@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
                disabled={isRequestingOtp}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isRequestingOtp}>
              {isRequestingOtp ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Sending Code...
                </>
              ) : (
                <>
                  Send Verification Code
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="space-y-3">
            <div className="space-y-1">
              <label htmlFor="otp" className="text-xs font-medium text-foreground">
                6-digit Verification Code
              </label>
              <Input
                id="otp"
                type="text"
                inputMode="numeric"
                maxLength={6}
                placeholder="123456"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                autoFocus
                disabled={isVerifyingOtp}
                className="text-center tracking-widest text-lg font-mono"
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isVerifyingOtp}>
              {isVerifyingOtp ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                "Verify & Sign In"
              )}
            </Button>
          </form>
        )}
      </CardContent>

      <CardFooter className="flex flex-col items-center justify-center border-t px-6 py-3 bg-muted/30 text-xs text-muted-foreground">
        {step === "verify" ? (
          <button
            type="button"
            onClick={() => {
              setStep("request")
              setOtp("")
              setFeedback({ type: null, text: "" })
            }}
            className="hover:underline text-primary font-medium focus:outline-none"
          >
            ← Use a different email address
          </button>
        ) : (
          <span>Passwordless & secure. No passwords or resets required.</span>
        )}
      </CardFooter>
    </Card>
  )
}
