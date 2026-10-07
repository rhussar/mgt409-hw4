import { FormEvent, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { AccountUser } from './AccountPage'

type ChatProduct = {
  product_id: string
  name: string
  garment_type: string
  description: string
  image_url: string
  price: number
  total_stock: number
}

type ChatMessage = {
  role: 'assistant' | 'user'
  text: string
  products?: ChatProduct[]
}

type Props = {
  open: boolean
  setOpen: (open: boolean) => void
  draft: string
  setDraft: (draft: string) => void
  user: AccountUser | null
  pageProductId: string | null
}

const welcome: ChatMessage = {
  role: 'assistant',
  text: 'Hi! Looking for a campus favorite? Ask me about styles, prices, or sizes.',
}

function ChatText({ text }: { text: string }) {
  return <>{text.split('\n').filter(line => line.trim()).map((line, lineIndex) =>
    <span className={line.trim().startsWith('- ') ? 'chat-line chat-list-line' : 'chat-line'} key={lineIndex}>
      {line.split(/(\*\*[^*]+\*\*)/g).map((part, partIndex) => part.startsWith('**') && part.endsWith('**')
        ? <strong key={partIndex}>{part.slice(2, -2)}</strong>
        : <span key={partIndex}>{part}</span>)}
    </span>,
  )}</>
}

export default function ChatWidget({ open, setOpen, draft, setDraft, user, pageProductId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([welcome])
  const [pending, setPending] = useState(false)
  const messagesEnd = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let active = true
    if (!user) {
      setMessages([welcome])
      return
    }
    fetch('/api/chat/history', { credentials: 'same-origin' })
      .then(response => response.ok ? response.json() : [])
      .then((items: Array<{ role: 'assistant' | 'user'; content: string; products: ChatProduct[] }>) => {
        if (active) setMessages(items.length ? items.map(item => ({ role: item.role, text: item.content, products: item.products })) : [welcome])
      })
      .catch(() => { if (active) setMessages([welcome]) })
    return () => { active = false }
  }, [user?.id])

  useEffect(() => {
    if (open) messagesEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, open])

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || pending) return
    setMessages(current => [...current, { role: 'user', text }])
    setDraft('')
    setPending(true)
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ message: text, page_product_id: pageProductId }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'The assistant is unavailable right now.')
      setMessages(current => [...current, { role: 'assistant', text: data.reply, products: data.products }])
    } catch (error) {
      setMessages(current => [...current, { role: 'assistant', text: error instanceof Error ? error.message : 'The assistant is unavailable right now.' }])
    } finally {
      setPending(false)
    }
  }

  return <div className="chat-anchor">
    {open && <section className="chat-panel" aria-label="Campus Customs chat">
      <div className="chat-header"><div><span className="chat-dot" /><strong>Campus Customs</strong><small>Shop assistant</small></div><button aria-label="Close chat" onClick={() => setOpen(false)} type="button">×</button></div>
      <div className="chat-messages" aria-live="polite">
        {messages.map((message, index) => <div className={`chat-turn ${message.role}`} key={`${index}-${message.role}`}>
          <p className={`chat-bubble ${message.role}`}><ChatText text={message.text} /></p>
          {message.products && message.products.length > 0 && <div className="chat-results" aria-label="Matching products">
            <span className="chat-results-label">Matching pieces · {message.products.length}</span>
            <div className="chat-results-list">{message.products.map(product => <Link className="chat-product" key={product.product_id} to={`/products/${product.product_id}`}>
              <img alt={product.name} src={product.image_url} />
              <span><strong>{product.name}</strong><small>{product.garment_type}</small><b>${product.price.toFixed(2)}</b></span>
              <span aria-hidden="true">↗</span>
            </Link>)}</div>
          </div>}
        </div>)}
        {pending && <p className="chat-thinking" role="status">Checking the catalogue…</p>}
        <div ref={messagesEnd} />
      </div>
      <form className="chat-compose" onSubmit={send}><label className="sr-only" htmlFor="chat-input">Message</label><input id="chat-input" maxLength={1000} onChange={event => setDraft(event.target.value)} placeholder="Ask about styles or stock…" value={draft} /><button aria-label="Send message" disabled={!draft.trim() || pending} type="submit">↑</button></form>
      {user && <div className="chat-saved-note">Conversation saved to your account</div>}
    </section>}
    <button aria-expanded={open} aria-label={open ? 'Close chat' : 'Open chat'} className="chat-toggle" onClick={() => setOpen(!open)} type="button">{open ? '×' : '✦'}<span>{open ? 'Close' : 'Ask us'}</span></button>
  </div>
}
