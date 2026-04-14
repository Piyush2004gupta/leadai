import { useState, useEffect } from 'react'
import { api } from '../hooks/api'

export default function StatsPage() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api.stats().then(setStats)
    const iv = setInterval(() => api.stats().then(setStats), 5000)
    return () => clearInterval(iv)
  }, [])

  const cards = stats ? [
    { label:'Total Inventory',   value: stats.total,    color:'var(--text)',   icon:'◈', glow:'rgba(255,255,255,0.03)' },
    { label:'Pending Protocol',  value: stats.pending,  color:'var(--muted)',  icon:'⌛', glow:'rgba(100,100,100,0.03)' },
    { label:'Transmission OK',   value: stats.sent,     color:'var(--accent)', icon:'⚡', glow:'var(--accent-glow)' },
    { label:'Response Ratio',    value: stats.sent > 0 ? `${Math.round((stats.replied||0)/stats.sent*100)}%` : '0%', color:'#38BDF8', icon:'📈', glow:'rgba(56,189,248,0.05)' },
  ] : []

  return (
    <div className="fade-up">
      <div style={{ marginBottom:40 }}>
        <div style={{ fontSize:10, color:'var(--accent)', letterSpacing:'.35em', fontWeight:900, marginBottom:8 }}>SYSTEM_ANALYTICS</div>
        <div style={{ fontFamily:'var(--font-display)', fontSize:28, fontWeight:800, letterSpacing:'-0.03em' }}>Command Center</div>
        <div style={{ color:'var(--muted)', fontSize:13, marginTop:4, opacity:0.8 }}>Real-time telemetry and outreach synchronization.</div>
      </div>

      {!stats ? (
        <div style={{ color:'var(--muted)', textAlign:'center', padding:80, fontFamily:'var(--font-mono)', fontSize:12 }}>[ ESTABLISHING DATA LINK ]</div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:24 }}>
          
          {/* Quick Metrics */}
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:16 }}>
            {cards.map(c => (
              <div key={c.label} className="card glass" style={{
                padding:'20px 24px', position:'relative', overflow:'hidden',
                background:c.glow
              }}>
                <div style={{ fontSize:15, marginBottom:12, opacity:0.8 }}>{c.icon}</div>
                <div style={{ fontFamily:'var(--font-display)', fontSize:28, fontWeight:800, color:c.color, lineHeight:1, letterSpacing:'-0.04em' }}>{c.value}</div>
                <div style={{ fontSize:9, color:'var(--muted)', marginTop:10, fontWeight:700, letterSpacing:'.12em' }}>{c.label.toUpperCase()}</div>
                <div style={{ position:'absolute', bottom:-10, right:-10, width:60, height:60, background:c.color, filter:'blur(40px)', opacity:0.04 }} />
              </div>
            ))}
          </div>

          <div style={{ display:'grid', gridTemplateColumns:'1.5fr 1fr', gap:24 }}>
            
            {/* Conversion Funnel */}
            <div className="card glass" style={{ padding: 28 }}>
               <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:28 }}>
                  <div style={{ width:28, height:28, background:'rgba(56,189,248,0.08)', borderRadius:8, display:'flex', alignItems:'center', justifyContent:'center', color:'#38BDF8', fontSize:14 }}>📈</div>
                  <div style={{ fontSize:12, fontWeight:800, letterSpacing:'.08em' }}>OUTREACH FUNNEL</div>
               </div>

               <div style={{ display:'flex', flexDirection:'column', gap:24 }}>
                {[
                  { label:'Harvested', val:stats.total,   color:'var(--muted)',  desc:'Verified unique entities' },
                  { label:'Transmitted', val:stats.sent,    color:'var(--accent)', desc:'Protocol deliveries' },
                  { label:'Engagements', val:stats.replied||0, color:'#38BDF8',   desc:'Reply interactions' },
                ].map(row => (
                  <div key={row.label}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:10 }}>
                      <div>
                        <div style={{ fontSize:12, fontWeight:700, color:'var(--text)' }}>{row.label}</div>
                        <div style={{ fontSize:10, color:'var(--muted)', marginTop:2, opacity:0.6 }}>{row.desc}</div>
                      </div>
                      <div style={{ fontFamily:'var(--font-display)', fontSize:18, fontWeight:800, color:row.color }}>{row.val}</div>
                    </div>
                    <div style={{ height:5, background:'var(--border)', borderRadius:10, overflow:'hidden' }}>
                      <div style={{
                        height:'100%', borderRadius:10, background:row.color,
                        width: `${stats.total > 0 ? Math.round(row.val/stats.total*100) : 0}%`,
                        transition:'width 1s cubic-bezier(0.1, 0.7, 1.0, 0.1)',
                        boxShadow: `0 0 10px ${row.color}33`
                      }}/>
                    </div>
                  </div>
                ))}
               </div>
            </div>

            {/* Performance Insights */}
            <div className="card" style={{ background:'var(--surface-item)', padding: 28 }}>
               <div style={{ fontSize:10, fontWeight:800, color:'var(--muted)', letterSpacing:'.12em', marginBottom:20 }}>PLATFORM INSIGHTS</div>
               
               <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
                  <div className="glass" style={{ padding:16, borderRadius:12 }}>
                     <div style={{ color:'var(--accent)', fontSize:10, fontWeight:900, marginBottom:4 }}>NODE ADVISORY</div>
                     <div style={{ color:'var(--text)', fontSize:12, lineHeight:1.5, opacity:0.9 }}>
                        Detected {stats.sent > 0 ? 'active conversion' : 'ready queue'}. Recommend {stats.pending > 0 ? 'transmission burst' : 'new scan'} for peak ROI.
                     </div>
                  </div>

                  <div style={{ padding:'0 4px', marginTop:4 }}>
                    <div style={{ fontSize:9, color:'var(--muted)', marginBottom:10, fontWeight:700, letterSpacing:'.05em' }}>SESSION RUNTIME</div>
                    <div style={{ fontSize:18, fontWeight:800, color:'var(--text)' }}>1h 24m</div>
                    <div style={{ height:1, background:'var(--border)', margin:'12px 0', opacity:0.5 }} />
                    <div style={{ fontSize:9, color:'var(--muted)', marginBottom:10, fontWeight:700, letterSpacing:'.05em' }}>RESPONSE LATENCY</div>
                    <div style={{ fontSize:18, fontWeight:800, color:'var(--text)' }}>4.2m</div>
                  </div>
               </div>
            </div>

          </div>
        </div>
      )}
    </div>
  )
}
