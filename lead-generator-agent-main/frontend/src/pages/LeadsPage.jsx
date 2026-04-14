import { useState, useEffect } from 'react'
import { api } from '../hooks/api'

const STATUS_STYLE = {
  pending:  { bg:'#1A2235', color:'#4A5568' },
  sent:     { bg:'#0A1F12', color:'#4DFFA0' },
  failed:   { bg:'#1A0A0A', color:'#EF4444' },
  replied:  { bg:'#0A0F1F', color:'#3B82F6' },
}

export default function LeadsPage() {
  const [leads,   setLeads]   = useState([])
  const [loading, setLoading] = useState(true)
  const [search,  setSearch]  = useState('')
  const [filter,  setFilter]  = useState('all')
  const [sending, setSending] = useState(false)
  const [jobId,   setJobId]   = useState(null)
  const [job,     setJob]     = useState(null)

  // Added state for Quick Run compatibility
  const [category, setCategory] = useState('gym')
  const [city,     setCity]     = useState('faridabad')
  const [area,     setArea]     = useState('')
  const [script,   setScript]   = useState('hello')

  const runAgent = async () => {
    setSending(true);
  
    try {
      const res = await fetch("https://lead-generator-agent-1.onrender.com/run-agent", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          category,
          city,
          area,
          script
        })
      });
  
      const data = await res.json();
      console.log(data);
  
      if (data.job_id) {
        setJobId(data.job_id);
      }
  
    } catch (err) {
      console.error(err);
    }
  
    setSending(false);
  };

  const load = async () => {
    setLoading(true)
    const r = await api.leads()
    setLeads(r.leads || [])
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  // Poll sending job
  useEffect(() => {
    if (!jobId) return
    const iv = setInterval(async () => {
      const j = await api.job(jobId)
      setJob(j)
      if (j.status === 'done' || j.status === 'error') {
        clearInterval(iv)
        setSending(false)
        load()
      }
    }, 2000)
    return () => clearInterval(iv)
  }, [jobId])

  const handleSend = async () => {
    const pendingCount = leads.filter(l => l.status === 'pending' && l.message).length
    if (pendingCount === 0) {
      alert("No pending leads with messages found.")
      return
    }
    if (!confirm(`Are you sure you want to start outreach for ${pendingCount} leads?`)) return
    
    setSending(true)
    const res = await api.send()
    setJobId(res.job_id)
  }

  const filtered = leads.filter(l => {
    const matchSearch = !search || l.name?.toLowerCase().includes(search.toLowerCase()) || l.phone?.includes(search)
    const matchFilter = filter === 'all' || (filter === 'with_site' ? l.has_website : l.status === filter)
    return matchSearch && matchFilter
  })

  return (
    <div className="fade-up">
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:40 }}>
        <div>
          <div style={{ fontSize:11, color:'var(--accent)', letterSpacing:'.3em', fontWeight:800, marginBottom:8 }}>DATABASE</div>
          <div style={{ fontFamily:'var(--font-display)', fontSize:32, fontWeight:800, letterSpacing:'-0.02em' }}>Intelligence Pool</div>
          <div style={{ color:'var(--muted)', fontSize:14, marginTop:4 }}>
            {leads.length} leads harvested {job && `| ACTIVE OUTREACH: ${job.progress}%`}
          </div>
        </div>
        <div style={{ display:'flex', gap:10 }}>
          <button onClick={runAgent} className="btn-secondary" style={{ padding:'10px 20px', background:'var(--accent-glow)', color:'var(--accent)', borderStyle:'dashed' }}>
            Run Agent 🚀
          </button>
          <button onClick={handleSend} disabled={sending} className="btn-primary" style={{ padding:'10px 20px' }}>
            {sending ? '📲 TRANSMITTING...' : '🚀 START OUTREACH'}
          </button>
          <button onClick={load} className="btn-secondary" style={{ padding:'10px 20px' }}>↺ Refresh</button>
          <button onClick={async()=>{ if(confirm('Wipe database?')){ await api.reset(); load() } }}
            className="btn-secondary" style={{ color:'#f87171', borderColor:'#451a1a', padding:'10px 20px' }}>
            ✕ Reset
          </button>
        </div>
      </div>

      <div className="card glass" style={{ padding: '8px', marginBottom: 24 }}>
        <div style={{ display:'flex', gap:8, alignItems:'center' }}>
          <div style={{ padding:'0 14px', color:'var(--muted)' }}>🔍</div>
          <input placeholder="Filter by name, phone or category..." value={search}
            onChange={e=>setSearch(e.target.value)}
            style={{ background:'transparent', border:'none', padding:'12px 0' }} />
          <div style={{ display:'flex', gap:6, paddingRight:8 }}>
            {['all','pending','sent','failed','with_site'].map(f => (
              <button key={f} onClick={()=>setFilter(f)}
                style={{
                  background: filter===f ? 'var(--accent)' : 'transparent',
                  color:      filter===f ? '#000' : 'var(--muted)',
                  padding:'6px 12px', fontSize:11, borderRadius:6, fontWeight:700
                }}>
                {f.replace('_',' ').toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table Header */}
      <div style={{
        display:'grid', gridTemplateColumns:'2.5fr 1.2fr 80px 1.8fr 1.2fr 100px',
        gap:16, padding:'10px 24px', fontSize:10, color:'var(--muted)', fontWeight:800, letterSpacing:'.1em'
      }}>
        <span>LEAD IDENTIFIER</span>
        <span>CONTACT</span>
        <span>RATING</span>
        <span>GEOGRAPHIC DATA</span>
        <span>DIGITAL ASSETS</span>
        <span style={{ textAlign:'right' }}>PROTOCOL</span>
      </div>

      {/* Table Body */}
      {loading ? (
        <div style={{ color:'var(--muted)', textAlign:'center', padding:80, fontFamily:'var(--font-mono)' }}>[ INITIALIZING DATA ]</div>
      ) : filtered.length === 0 ? (
        <div style={{ color:'var(--muted)', textAlign:'center', padding:80, border:'1px dashed var(--border)', borderRadius:12 }}>
          Zero leads detected. Start a new mission.
        </div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
          {filtered.map((l, i) => (
            <div key={i} className="card glass" style={{
              borderRadius:12, padding:'16px 24px',
              display:'grid', gridTemplateColumns:'2.5fr 1.2fr 80px 1.8fr 1.2fr 100px',
              gap:16, alignItems:'center', cursor:'default'
            }}>
              <div style={{ overflow:'hidden' }}>
                <div style={{ fontWeight:700, color:'var(--text)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{l.name}</div>
                <div style={{ fontSize:10, color:'var(--accent)', marginTop:2, fontWeight:800, opacity:0.8 }}>{l.category?.toUpperCase()}</div>
              </div>
              <div style={{ fontFamily:'var(--font-mono)', color:'#CBD5E1', fontSize:12 }}>{l.phone}</div>
              <div style={{ fontSize:12, color:'var(--muted)', fontWeight:700 }}>
                {l.rating ? `⭐ ${l.rating}` : '—'}
              </div>
              <div style={{ fontSize:11, color:'var(--muted)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', opacity:0.7 }} title={l.address}>
                {l.address || '—'}
              </div>
              <div style={{ fontSize:11 }}>
                {l.website ? (
                  <a href={l.website} target="_blank" rel="noopener noreferrer" style={{ color:'var(--accent)', textDecoration:'none', fontWeight:600 }}>
                    🌐 SOURCE
                  </a>
                ) : (
                  <span style={{ opacity:0.3 }}>NULL</span>
                )}
              </div>
              <div style={{ display:'flex', justifyContent:'flex-end' }}>
                <div style={{
                  padding:'5px 12px', borderRadius:6, fontSize:10, fontWeight:800, textAlign:'center',
                  background: STATUS_STYLE[l.status]?.bg || '#1e293b',
                  color:      STATUS_STYLE[l.status]?.color || '#94a3b8',
                  letterSpacing:'.05em', border: `1px solid ${STATUS_STYLE[l.status]?.color}22`
                }}>
                  {(l.status || 'pending').toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
