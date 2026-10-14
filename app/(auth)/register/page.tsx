import Link from 'next/link'
import { signup, googleSignIn } from './actions'

export default async function RegisterPage(props: {
  searchParams: Promise<{ error?: string }>
}) {
  const { error } = await props.searchParams

  return (
    <div className="w-full max-w-sm rounded-xl border border-border bg-bg-card p-6">
      <h1 className="text-2xl font-semibold text-text-primary">Register</h1>
      <p className="mt-1 text-sm text-text-secondary">
        Create an account to start practicing.
      </p>

      {error && (
        <p className="mt-4 rounded-lg border border-status-error/30 bg-status-error/10 px-3 py-2 text-sm text-status-error">
          {error}
        </p>
      )}

      <form action={signup} className="mt-6 flex flex-col gap-4">
        <div>
          <label htmlFor="email" className="text-[13px] font-medium text-text-secondary">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@example.com"
            className="mt-1 w-full rounded-lg border border-border bg-bg-card-secondary px-4 py-3 text-[15px] text-text-primary placeholder:text-text-muted focus:border-border-focus focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor="password" className="text-[13px] font-medium text-text-secondary">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            autoComplete="new-password"
            placeholder="At least 6 characters"
            className="mt-1 w-full rounded-lg border border-border bg-bg-card-secondary px-4 py-3 text-[15px] text-text-primary placeholder:text-text-muted focus:border-border-focus focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor="confirmPassword" className="text-[13px] font-medium text-text-secondary">
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            required
            autoComplete="new-password"
            placeholder="Re-enter your password"
            className="mt-1 w-full rounded-lg border border-border bg-bg-card-secondary px-4 py-3 text-[15px] text-text-primary placeholder:text-text-muted focus:border-border-focus focus:outline-none"
          />
        </div>

        <button
          type="submit"
          className="mt-2 rounded-lg bg-accent px-6 py-3 text-[15px] font-medium text-text-inverse transition-colors hover:bg-accent-dark"
        >
          Create Account
        </button>
      </form>

      <div className="mt-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-border" />
        <span className="text-[13px] text-text-muted">or</span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <form action={googleSignIn} className="mt-6">
        <button
          type="submit"
          className="w-full rounded-lg border border-border bg-transparent px-6 py-3 text-[15px] font-medium text-text-secondary transition-all hover:border-text-muted hover:text-text-primary"
        >
          Continue with Google
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-text-secondary">
        Already have an account?{' '}
        <Link
          href="/login"
          className="font-medium text-accent no-underline transition-colors hover:text-accent-dark"
        >
          Log In
        </Link>
      </p>
    </div>
  )
}
