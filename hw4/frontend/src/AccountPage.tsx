import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

export type AccountUser = {
  id: number
  name: string
  first_name: string | null
  last_name: string | null
  email: string
  created_at: string
}

type Props = {
  mode: 'login' | 'create'
  onAuth: (user: AccountUser) => void
}

export default function AccountPage({ mode, onAuth }: Props) {
  const [message, setMessage] = useState('')
  const [pending, setPending] = useState(false)
  const navigate = useNavigate()
  const isCreate = mode === 'create'

  useEffect(() => { setMessage('') }, [mode])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const fields = new FormData(form)
    const password = String(fields.get('password') ?? '')
    if (isCreate && password !== String(fields.get('confirm_password') ?? '')) {
      setMessage('Passwords do not match. Please try again.')
      return
    }

    const body = isCreate ? {
      first_name: String(fields.get('first_name') ?? ''),
      last_name: String(fields.get('last_name') ?? ''),
      email: String(fields.get('email') ?? ''),
      password,
    } : { email: String(fields.get('email') ?? ''), password }

    setPending(true)
    setMessage('')
    try {
      const response = await fetch(isCreate ? '/api/auth/register' : '/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(body),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check your information and try again.')
      onAuth(data.user as AccountUser)
      form.reset()
      navigate('/')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Something went wrong. Please try again.')
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="shell account-page">
      <div className="account-aside">
        <span className="eyebrow">Your campus, your way</span>
        <h1>Come on in.</h1>
        <p>Sign in to keep your conversations with the shop assistant close at hand.</p>
        <span className="account-monogram" aria-hidden="true">CC</span>
      </div>
      <div className="account-card">
        <span className="eyebrow">{isCreate ? 'Join Campus Customs' : 'Welcome back'}</span>
        <h2>{isCreate ? 'Create an account' : 'Log in'}</h2>
        <p>{isCreate ? 'Make a profile to save your chat history.' : 'Good to see you again.'}</p>
        <form onSubmit={handleSubmit}>
          {isCreate && <div className="name-fields">
            <label>First name<input autoComplete="given-name" name="first_name" placeholder="First name" required /></label>
            <label>Last name<input autoComplete="family-name" name="last_name" placeholder="Last name" required /></label>
          </div>}
          <label>Email address<input autoComplete="email" name="email" placeholder="you@example.com" required type="email" /></label>
          <label>Password<input autoComplete={isCreate ? 'new-password' : 'current-password'} minLength={isCreate ? 8 : undefined} name="password" placeholder={isCreate ? 'At least 8 characters' : 'Your password'} required type="password" /></label>
          {isCreate && <label>Confirm password<input autoComplete="new-password" minLength={8} name="confirm_password" placeholder="Enter it again" required type="password" /></label>}
          <button className="button button-dark" disabled={pending} type="submit">{pending ? 'Please wait…' : isCreate ? 'Create account' : 'Log in'} <span aria-hidden="true">↗</span></button>
        </form>
        {message && <p className="account-message" role="alert">{message}</p>}
        <p className="account-switch">{isCreate ? 'Already have an account?' : 'New around here?'} <Link to={isCreate ? '/login' : '/create-account'}>{isCreate ? 'Log in' : 'Create an account'}</Link></p>
      </div>
    </main>
  )
}
