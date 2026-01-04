import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Authentication - Stock Predictor',
  description: 'Sign in or create an account for Stock Predictor',
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Auth pages have minimal layout - no navbar or sidebar
  return <>{children}</>
}
