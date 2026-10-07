import { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useParams } from 'react-router-dom'
import AccountPage, { type AccountUser } from './AccountPage'
import ChatWidget from './ChatWidget'

type Stock = { size: string; quantity: number }
type Product = {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  inventory: Stock[]
  total_stock: number
}

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

function categoryFor(product: Product) {
  const type = product.garment_type.toLowerCase()
  if (type.includes('hoodie') || type.includes('hood')) return 'Hoodies'
  if (type.includes('t-shirt') || type.includes('tee')) return 'T-Shirts'
  if (type.includes('crewneck') || type.includes('sweatshirt')) return 'Crewnecks'
  if (type.includes('jacket') || type.includes('fleece') || type.includes('zip')) return 'Layers'
  return 'Other'
}

function ProductCard({ product }: { product: Product }) {
  return (
    <Link className="product-card" to={`/products/${product.product_id}`} aria-label={`View ${product.name}`}>
      <div className="product-card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        <span className="product-card-view">View details <span aria-hidden="true">↗</span></span>
      </div>
      <div className="product-card-meta">
        <span className="eyebrow">{product.garment_type}</span>
        <span className="product-card-price">{currency.format(product.price)}</span>
      </div>
      <h3>{product.name}</h3>
      <p>{product.description}</p>
    </Link>
  )
}

function ProductGrid({ products }: { products: Product[] }) {
  return <div className="product-grid">{products.map(product => <ProductCard key={product.product_id} product={product} />)}</div>
}

function HomePage({ products, loading, error }: { products: Product[]; loading: boolean; error: string }) {
  const picks = useMemo(() => {
    const preferred = ['basic-hoodie-big-yale', 'boola-boola-t-shirt', 'brooks-brothers-bomber-jacket-yale', 'champion-reverse-weave-crewneck']
    return preferred.map(id => products.find(product => product.product_id === id)).filter((product): product is Product => Boolean(product))
  }, [products])
  const hero = products.find(product => product.product_id === 'basic-hoodie-big-yale') ?? products[0]

  return (
    <main>
      <section className="hero shell">
        <div className="hero-copy">
          <span className="eyebrow hero-eyebrow"><span className="eyebrow-line" /> Made for your campus days</span>
          <h1>Wear your <em>Yale</em> story.</h1>
          <p>From first walks across Old Campus to the traditions you carry with you, find pieces that feel like your kind of Bulldog spirit.</p>
          <Link className="button button-light" to="/products">Explore the collection <span aria-hidden="true">↗</span></Link>
          <div className="hero-footer"><span>01 / 03</span><span>Campus favorites, all in one place</span></div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="hero-shape hero-shape-one" />
          <div className="hero-shape hero-shape-two" />
          {hero && <img src={hero.image_url} alt="" />}
          <div className="hero-caption"><span>THE EVERYDAY EDIT</span><strong>Classic spirit.<br />Your own style.</strong></div>
        </div>
      </section>

      <section className="intro-band">
        <div className="shell intro-band-inner"><span>✦</span><p>Campus roots. Everyday comfort. A little extra Yale pride.</p><span>✦</span></div>
      </section>

      <section className="section shell" aria-labelledby="featured-heading">
        <div className="section-heading"><div><span className="eyebrow">Curated for campus</span><h2 id="featured-heading">The good stuff</h2></div><Link className="text-link" to="/products">Shop all products <span aria-hidden="true">↗</span></Link></div>
        {error ? <p className="error-message" role="alert">{error}</p> : loading ? <p className="status">Loading favorites…</p> : <ProductGrid products={picks.length ? picks : products.slice(0, 4)} />}
      </section>

      <section className="story-section shell">
        <div className="story-mark">Y</div>
        <div><span className="eyebrow">Made for the moments</span><h2>More than a school color.</h2><p>Game day, study day, or any day in between. Find a piece that goes wherever your Yale story takes you.</p><Link className="button button-outline" to="/about">Get to know us <span aria-hidden="true">↗</span></Link></div>
      </section>
    </main>
  )
}

function ProductsPage({ products, loading, error }: { products: Product[]; loading: boolean; error: string }) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [size, setSize] = useState('')
  const [sort, setSort] = useState('name')
  const [visibleCount, setVisibleCount] = useState(12)
  const categories = ['All', 'Hoodies', 'T-Shirts', 'Crewnecks', 'Layers', 'Other']
  const filtered = useMemo(() => {
    const matches = products.filter(product => {
      const matchesCategory = category === 'All' || categoryFor(product) === category
      const matchesSize = !size || product.inventory.some(item => item.size === size && item.quantity > 0)
      const haystack = [product.name, product.garment_type, product.description, ...product.colors, ...product.search_tags].join(' ').toLowerCase()
      return matchesCategory && matchesSize && haystack.includes(query.trim().toLowerCase())
    })
    return matches.sort((a, b) => sort === 'price-low' ? a.price - b.price || a.name.localeCompare(b.name)
      : sort === 'price-high' ? b.price - a.price || a.name.localeCompare(b.name)
      : a.name.localeCompare(b.name))
  }, [products, query, category, size, sort])

  useEffect(() => { setVisibleCount(12) }, [query, category, size, sort])

  function clearFilters() {
    setQuery('')
    setCategory('All')
    setSize('')
    setSort('name')
  }

  return (
    <main className="shell catalogue-page">
      <div className="page-hero"><span className="eyebrow">The collection</span><h1>Find your campus favorite.</h1><p>Explore the colors, layers, and familiar details that make a look your own.</p></div>
      <div className="catalogue-toolbar"><div className="category-list" role="group" aria-label="Filter products by category">{categories.map(item => <button className={category === item ? 'category active' : 'category'} key={item} onClick={() => setCategory(item)} type="button">{item}</button>)}</div><label className="search-box"><span aria-hidden="true">⌕</span><span className="sr-only">Search products</span><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search the collection" type="search" /></label></div>
      <div className="shopping-tools">
        <label>My size is in stock<select aria-label="Filter by available size" onChange={event => setSize(event.target.value)} value={size}><option value="">Any size</option>{['XS', 'S', 'M', 'L', 'XL', 'XXL'].map(item => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Sort by<select aria-label="Sort products" onChange={event => setSort(event.target.value)} value={sort}><option value="name">Name A–Z</option><option value="price-low">Price: low to high</option><option value="price-high">Price: high to low</option></select></label>
        {(query || category !== 'All' || size || sort !== 'name') && <button className="clear-filters" onClick={clearFilters} type="button">Clear filters ×</button>}
      </div>
      <div className="result-count">{loading ? 'Loading products…' : `${filtered.length} ${filtered.length === 1 ? 'piece' : 'pieces'}`}</div>
      {error && <p className="error-message" role="alert">{error}</p>}
      {!loading && !error && filtered.length === 0 && <div className="empty-state"><h2>No pieces found</h2><p>Try a different search or browse the full collection.</p><button className="button button-dark" onClick={clearFilters} type="button">Clear filters</button></div>}
      <ProductGrid products={filtered.slice(0, visibleCount)} />
      {visibleCount < filtered.length && <button className="button button-outline load-more" onClick={() => setVisibleCount(count => count + 12)} type="button">Show more pieces <span aria-hidden="true">↓</span></button>}
    </main>
  )
}

function ProductPage({ products, loading, error, onChat }: { products: Product[]; loading: boolean; error: string; onChat: (product: Product) => void }) {
  const { productId } = useParams()
  const product = products.find(item => item.product_id === productId)
  if (loading) return <main className="shell product-page"><p className="status">Loading product…</p></main>
  if (error) return <main className="shell product-page"><p className="error-message" role="alert">{error}</p></main>
  if (!product) return <main className="shell product-page"><h1>We couldn't find that piece.</h1><Link className="button button-dark" to="/products">Back to products</Link></main>

  return (
    <main className="shell product-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb"><Link to="/">Home</Link><span>/</span><Link to="/products">Products</Link><span>/</span><span>{product.name}</span></nav>
      <div className="product-detail">
        <div className="product-photo"><img src={product.image_url} alt={product.name} /></div>
        <div className="product-info"><span className="eyebrow">{product.garment_type}</span><h1>{product.name}</h1><p className="detail-price">{currency.format(product.price)}</p><div className="divider" /><h2>About this piece</h2><p className="detail-description">{product.description}</p><p className="color-note"><strong>Colors:</strong> {product.colors.join(', ')}</p><div className="divider" /><div className="stock-heading"><h2>Sizes & availability</h2><span>{product.total_stock > 0 ? 'In stock' : 'Sold out'}</span></div><div className="size-grid">{product.inventory.map(item => <div className={item.quantity > 0 ? 'size-option' : 'size-option sold-out'} key={item.size}><strong>{item.size}</strong><span>{item.quantity > 0 ? `${item.quantity} left` : 'Out'}</span></div>)}</div><p className="stock-note">Availability comes from the Campus Customs catalogue and may change.</p><button className="button button-dark detail-chat" onClick={() => onChat(product)} type="button">Ask about this piece <span aria-hidden="true">↗</span></button></div>
      </div>
      <section className="related-section"><div className="section-heading"><div><span className="eyebrow">Keep looking</span><h2>You might also like</h2></div><Link className="text-link" to="/products">View all <span aria-hidden="true">↗</span></Link></div><ProductGrid products={products.filter(item => item.product_id !== product.product_id && categoryFor(item) === categoryFor(product)).slice(0, 4)} /></section>
    </main>
  )
}

function AboutPage() {
  return <main className="shell about-page"><div className="about-heading"><span className="eyebrow">Our story</span><h1>For the place that stays with you.</h1><p>Campus Customs celebrates the easy, unmistakable feeling of Yale: familiar blue, proud traditions, and something for the everyday moments in between.</p></div><div className="about-panels"><div className="about-panel blue-panel"><span>01 / CAMPUS SPIRIT</span><h2>Wear it your way.</h2><p>Classic collegiate pieces, fresh favorites, and the details that remind you where your story began.</p></div><div className="about-panel cream-panel"><span>02 / EVERYDAY STYLE</span><h2>Made to live in.</h2><p>Browse comfortable layers and standout graphics for class, the weekend, and wherever you go next.</p></div></div><div className="about-cta"><h2>Your next favorite is here.</h2><Link className="button button-dark" to="/products">Explore products <span aria-hidden="true">↗</span></Link></div></main>
}

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

export default function App() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatDraft, setChatDraft] = useState('')
  const [user, setUser] = useState<AccountUser | null>(null)
  const { pathname } = useLocation()

  useEffect(() => {
    let cancelled = false
    fetch('/api/products').then(async response => {
      if (!response.ok) throw new Error('The catalogue is unavailable right now. Please check that the backend is running.')
      return response.json() as Promise<Product[]>
    }).then(data => { if (!cancelled) setProducts(data) }).catch((reason: Error) => { if (!cancelled) setError(reason.message) }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])
  useEffect(() => { setMenuOpen(false) }, [pathname])
  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'same-origin' })
      .then(response => response.ok ? response.json() : null)
      .then(data => { if (data?.user) setUser(data.user as AccountUser) })
      .catch(() => { /* Guests can still browse and chat. */ })
  }, [])

  async function logout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' })
    } finally {
      setUser(null)
      setChatOpen(false)
    }
  }

  function openChat(product: Product) {
    setChatDraft(`Can you tell me about ${product.name}?`)
    setChatOpen(true)
  }

  return <>
    <ScrollToTop />
    <div className="announcement">CAMPUS STYLE, EVERY DAY <span aria-hidden="true">✦</span> EXPLORE THE COLLECTION</div>
    <header className="site-header"><div className="shell header-inner">
      <Link className="brand" to="/" aria-label="Campus Customs home"><span className="brand-mark">C<span>✦</span>C</span><span className="brand-name">CAMPUS<br />CUSTOMS</span></Link>
      <button aria-label="Toggle menu" aria-expanded={menuOpen} className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)} type="button">{menuOpen ? '×' : '☰'}</button>
      <nav aria-label="Main navigation" className={menuOpen ? 'nav-links open' : 'nav-links'}>
        <NavLink to="/" end>Home</NavLink><NavLink to="/products">Products</NavLink><NavLink to="/about">About Us</NavLink>
        {user ? <><span className="nav-greeting">Hi, {user.first_name || user.name}</span><button className="nav-account" onClick={logout} type="button">Log out <span aria-hidden="true">↗</span></button></> : <><NavLink to="/login">Log in</NavLink><NavLink className="nav-account" to="/create-account">Create account <span aria-hidden="true">↗</span></NavLink></>}
      </nav>
    </div></header>
    <Routes>
      <Route path="/" element={<HomePage products={products} loading={loading} error={error} />} />
      <Route path="/products" element={<ProductsPage products={products} loading={loading} error={error} />} />
      <Route path="/products/:productId" element={<ProductPage products={products} loading={loading} error={error} onChat={openChat} />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/login" element={<AccountPage mode="login" onAuth={setUser} />} />
      <Route path="/create-account" element={<AccountPage mode="create" onAuth={setUser} />} />
      <Route path="*" element={<main className="shell not-found"><h1>Page not found</h1><Link className="button button-dark" to="/">Back home</Link></main>} />
    </Routes>
    <footer className="site-footer"><div className="shell footer-inner"><div><div className="footer-brand">CAMPUS CUSTOMS<span>✦</span></div><p>Everyday pieces. Enduring campus spirit.</p></div><nav aria-label="Footer navigation"><Link to="/products">Products</Link><Link to="/about">About Us</Link><Link to="/login">Log in</Link></nav><small>Campus Customs · Yale-inspired storefront</small></div></footer>
    <ChatWidget open={chatOpen} setOpen={setChatOpen} draft={chatDraft} setDraft={setChatDraft} user={user} pageProductId={pathname.startsWith('/products/') ? pathname.slice('/products/'.length) : null} />
  </>
}
