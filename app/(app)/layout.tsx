import Link from 'next/link'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { createClient } from '@/lib/supabase/server'

async function signOut() {
  'use server'

  const supabase = await createClient()
  await supabase.auth.signOut()
  revalidatePath('/', 'layout')
  redirect('/login')
}

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-full flex-col">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <Link
          href="/setup"
          className="text-base font-semibold text-text-primary no-underline"
        >
          Oral Exam Prep
        </Link>
        <div className="flex items-center gap-4">
          <Link
            href="/account"
            className="text-sm text-text-secondary no-underline transition-colors hover:text-text-primary"
          >
            Account
          </Link>
          <form action={signOut}>
            <button
              type="submit"
              className="text-sm text-text-secondary no-underline transition-colors hover:text-text-primary"
            >
              Sign Out
            </button>
          </form>
        </div>
      </header>
      <main className="flex flex-1 flex-col">{children}</main>
    </div>
  )
}
