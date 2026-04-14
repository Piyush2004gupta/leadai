import { useState, useEffect, useRef } from 'react'
import { api } from '../hooks/api'

const S = {
  label: { fontSize:10, color:'var(--muted)', letterSpacing:'.12em', fontWeight:700, display:'block', marginBottom:6 },
  card:  { background:'var(--surface)', border:'1px solid var(--border)', borderRadius:12, padding:22 },
}

const STATUS_COLOR = {
  queued:    '#4A5568',
  scraping:  '#3B82F6',
  analyzing: '#A78BFA',
  writing:   '#FB923C',
  sending:   '#4DFFA0',
  done:      '#4DFFA0',
  error:     '#EF4444',
}

export default function RunPage() {
  const [form,    setForm]    = useState({ category:'', state:'', city:'', area:'', limit: 10, base_message: '', attachment: null })
  const [jobId,   setJobId]   = useState(null)
  const [job,     setJob]     = useState(null)
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const logRef = useRef(null)

  // Poll job status
  useEffect(() => {
    if (!jobId) return
    const iv = setInterval(async () => {
      const j = await api.job(jobId)
      setJob(j)
      if (j.status === 'done' || j.status === 'error') clearInterval(iv)
    }, 1500)
    return () => clearInterval(iv)
  }, [jobId])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [job?.logs])

  const handleRun = async () => {
    if (!form.category || !form.city || !form.limit) return
    setLoading(true)
    setJob(null)
    setResult(null)
    
    // Combine location details for the scraper
    const location = [form.area, form.city, form.state].filter(Boolean).join(', ');

    const payload = {
      category: form.category,
      location: location,
      limit: form.limit,
      base_message: form.base_message
    }

    const res = await api.run(payload)
    setJobId(res.job_id)
    setResult(res.message) // Setting the result as requested
    setLoading(false)
  }

  const busy = job && !['done','error'].includes(job?.status)

  return (
    <div className="fade-up">
      {/* Header */}
      <div style={{ marginBottom:48 }}>
        <div style={{ fontSize:11, color:'var(--accent)', letterSpacing:'.3em', fontWeight:800, marginBottom:8 }}>ORCHESTRATOR</div>
        <div style={{ fontFamily:'var(--font-display)', fontSize:32, fontWeight:800, letterSpacing:'-0.02em' }}>Launch AI Outreach</div>
        <div style={{ color:'var(--muted)', fontSize:14, marginTop:8, maxWidth:600 }}>
          Configure your target audience and custom messaging. The agent will handle the rest, from discovery to personalized delivery.
        </div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1.2fr 1fr', gap:32, alignItems:'start' }}>

        {/* Configuration Card */}
        <div className="card glass">
          <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:32 }}>
            <div style={{ width:32, height:32, background:'var(--accent-glow)', borderRadius:8, display:'flex', alignItems:'center', justifyContent:'center', color:'var(--accent)' }}>⚙️</div>
            <div style={{ fontSize:14, fontWeight:700, letterSpacing:'.05em' }}>MISSION CONFIG</div>
          </div>

          <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
            <div>
              <label style={S.label}>TARGET CATEGORY</label>
              <input placeholder="e.g. Gyms, Dental Clinics..." value={form.category}
                onChange={e => setForm(p=>({...p, category:e.target.value}))} />
            </div>
            
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12 }}>
              <div>
                <label style={S.label}>STATE</label>
                <input placeholder="e.g. Punjab" value={form.state}
                  onChange={e => setForm(p=>({...p, state:e.target.value}))} />
              </div>
              <div>
                <label style={S.label}>CITY</label>
                <input placeholder="e.g. Ludhiana" value={form.city}
                  onChange={e => setForm(p=>({...p, city:e.target.value}))} />
              </div>
              <div>
                <label style={S.label}>AREA</label>
                <input placeholder="e.g. Sarabha Nagar" value={form.area}
                  onChange={e => setForm(p=>({...p, area:e.target.value}))} />
              </div>
            </div>

            <div>
              <label style={S.label}>PERSONALIZED DISPATCH SCRIPT (MANDATORY)</label>
              <textarea 
                placeholder="What exactly should the agent say? Your message will be prioritized." 
                value={form.base_message}
                onChange={e => setForm(p=>({...p, base_message:e.target.value}))}
                style={{ minHeight: 120, fontSize:13 }}
              />
            </div>

            {/* Media Attachment */}
            <div>
              <label style={S.label}>MEDIA ATTACHMENT (IMAGE/VIDEO/PDF)</label>
              <div style={{ 
                border:'2px dashed var(--border)', borderRadius:12, padding:20, textAlign:'center',
                background: form.attachment ? 'var(--accent-glow)' : 'transparent',
                borderColor: form.attachment ? 'var(--accent)' : 'var(--border)',
                transition: 'all 0.3s'
              }}>
                <input type="file" id="media-upload" hidden onChange={e => setForm(p=>({...p, attachment: e.target.files[0]}))} />
                <label htmlFor="media-upload" style={{ cursor:'pointer', display:'block' }}>
                  {form.attachment ? (
                    <div style={{ color:'var(--accent)', fontWeight:600 }}>
                      📎 {form.attachment.name} (Selected)
                    </div>
                  ) : (
                    <div style={{ color:'var(--muted)' }}>
                      Click to upload media attachment <br/>
                      <span style={{ fontSize:11, opacity:0.6 }}>(Optional)</span>
                    </div>
                  )}
                </label>
              </div>
            </div>

            <div>
              <label style={S.label}>AGENT REACH (LEAD LIMIT)</label>
              <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
                {[5, 10, 20, 30, 40, 50].map(v => (
                  <button key={v}
                    onClick={() => setForm(p => ({ ...p, limit: v }))}
                    style={{
                      flex: 1, minWidth: 54, padding: '10px 0',
                      background: form.limit === v ? 'var(--accent)' : 'var(--surface-item)',
                      color:      form.limit === v ? '#000' : 'var(--muted)',
                      border:     form.limit === v ? '1px solid var(--accent)' : '1px solid var(--border)',
                      fontWeight: 700, fontSize:12
                    }}>
                    {v}
                  </button>
                ))}
              </div>
            </div>

            <button onClick={handleRun} disabled={loading || busy} className="btn-primary"
              style={{ padding:'16px 0', fontSize:14, letterSpacing:'.1em', marginTop:12, fontWeight:800 }}>
              {loading ? 'INITIALIZING...' : busy ? `EXECUTING: ${job.status.toUpperCase()}` : 'START MY AGENT'}
            </button>
          </div>
        </div>

        {/* Console / Status */}
        <div className="card" style={{ background:'#030407', border:'1px solid var(--border)' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:24 }}>
             <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                <div style={{ width:10, height:10, borderRadius:'50%', background:busy ? 'var(--accent)' : 'var(--muted)' }} />
                <div style={{ fontSize:13, fontWeight:700, letterSpacing:'.05em' }}>MISSION CONSOLE</div>
             </div>
             {job && <div style={{ fontSize:18, fontWeight:900, color:'var(--accent)' }}>{job.progress}%</div>}
          </div>

          {!job ? (
            <div style={{ color:'var(--muted)', fontSize:13, padding:'40px 0', textAlign:'center', opacity:0.5 }}>
              Waiting for mission parameters...
            </div>
          ) : (
            <>
              {result && (
                <div style={{ 
                  background: 'var(--accent-glow)', 
                  border: '1px solid var(--accent)', 
                  padding: '12px', 
                  borderRadius: '8px', 
                  marginBottom: '16px',
                  color: 'var(--accent)',
                  fontSize: '13px',
                  fontWeight: 600
                }}>
                  ✨ {result}
                </div>
              )}

              <div style={{ height:4, background:'var(--border)', borderRadius:2, marginBottom:24, overflow:'hidden' }}>
                <div style={{ height:'100%', background:'var(--accent)', width: `${job.progress}%`, transition:'width .4s cubic-bezier(0.1, 0.7, 1.0, 0.1)' }}/>
              </div>

              <div ref={logRef} style={{
                background:'rgba(0,0,0,0.3)', borderRadius:8, padding:16, height:380, overflowY:'auto',
                fontFamily:'var(--font-mono)', fontSize:11, lineHeight:1.8, border:'1px solid var(--border)'
              }}>
                {(job.logs||[]).map((l,i) => (
                  <div key={i} style={{ marginBottom:6, display:'flex', gap:10 }}>
                    <span style={{ color:'var(--muted)', opacity:0.5 }}>[{l.time}]</span>
                    <span style={{ color: l.msg.includes('❌') ? '#f87171' : l.msg.includes('✅') ? 'var(--accent)' : '#94a3b8' }}>{l.msg}</span>
                  </div>
                ))}
              </div>

              {job.status === 'done' && (
                <div className="fade-up" style={{ marginTop:20, padding:16, background:'var(--accent-glow)', border:'1px solid var(--accent)', borderRadius:12 }}>
                   <div style={{ color:'var(--accent)', fontWeight:800, fontSize:14, marginBottom:4 }}>SUCCESSFUL MISSION</div>
                   <div style={{ color:'var(--text)', fontSize:12, opacity:0.9 }}>
                     Everything processed and messages are queued in leads.json.
                   </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
