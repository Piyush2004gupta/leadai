import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import RunPage     from './pages/RunPage'
import LeadsPage   from './pages/LeadsPage'
import StatsPage   from './pages/StatsPage'

const NAV = [
  { to: '/',       label: '▶ Run Agent' },
  { to: '/leads',  label: '◈ Leads'     },
  { to: '/stats',  label: '⬡ Stats'     },
]

function runAgent() {
  console.log("Button clicked");
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display:'flex', height:'100vh', background:'var(--bg)', overflow:'hidden' }}>

        {/* Sidebar */}
        <aside style={{
          width: 240, background:'var(--surface)', borderRight:'1px solid var(--border)',
          padding: '32px 16px', display:'flex', flexDirection:'column', gap:4,
          flexShrink: 0, height:'100vh'
        }}>
          {/* Logo */}
          <div style={{ marginBottom:40, paddingLeft:12 }}>
            <div style={{ fontSize:10, color:'var(--accent)', letterSpacing:'.25em', fontWeight:800, textTransform:'uppercase' }}>Platform</div>
            <div style={{ display:'flex', alignItems:'center', gap:8, marginTop:4 }}>
              <div style={{ width:24, height:24, background:'var(--accent)', borderRadius:6, display:'flex', alignItems:'center', justifyContent:'center', color:'#000', fontWeight:900, fontSize:14 }}>L</div>
              <div style={{ fontFamily:'var(--font-display)', fontSize:20, fontWeight:800, color:'var(--text)', letterSpacing:'-0.02em' }}>
                Lead<span style={{color:'var(--accent)'}}>Agent</span>
              </div>
            </div>
          </div>

          <div style={{ color:'var(--muted)', fontSize:11, fontWeight:700, padding:'0 12px 12px', letterSpacing:'.1em' }}>NAVIGATION</div>
          {NAV.map(n => (
            <NavLink key={n.to} to={n.to} end={n.to==='/'} style={({ isActive }) => ({
              display:'flex', alignItems:'center', gap:12, padding:'10px 14px', borderRadius:'10px',
              fontFamily:'var(--font-display)', fontWeight:600, fontSize:13,
              color: isActive ? 'var(--accent)' : 'var(--muted)',
              background: isActive ? 'var(--accent-glow)' : 'transparent',
              textDecoration:'none', transition:'all .2s cubic-bezier(0.4, 0, 0.2, 1)',
              border: isActive ? '1px solid var(--accent)' : '1px solid transparent'
            })}>
              <span style={{ fontSize:16 }}>{n.label.split(' ')[0]}</span>
              {n.label.split(' ').slice(1).join(' ')}
            </NavLink>
          ))}

          <div style={{ marginTop:'auto', display:'flex', flexDirection:'column', gap:8 }}>
            {/* Quick Test Button */}
            <button onClick={runAgent} className="btn-secondary" style={{ width:'100%', fontSize:11, padding:'8px 0', borderStyle:'dashed' }}>
              ⚡ Run AI Quick Test
            </button>

            <div style={{ padding:'16px', background:'var(--surface-item)', borderRadius:12, border:'1px solid var(--border)', position:'relative', overflow:'hidden' }}>
              <div style={{ position:'absolute', top:-20, right:-20, width:60, height:60, background:'var(--accent)', filter:'blur(40px)', opacity:0.1 }} />
              <div style={{ fontSize:10, color:'var(--muted)', marginBottom:6, fontWeight:700 }}>SYSTEM STATUS</div>
              <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                <div style={{ width:8, height:8, borderRadius:'50%', background:'var(--accent)', boxShadow:'0 0 10px var(--accent)', animation:'pulse 2s infinite' }}/>
                <span style={{ fontSize:12, color:'var(--text)', fontWeight:600 }}>Engine Online</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main style={{ flex:1, overflowY:'auto', padding:'40px 48px' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <Routes>
              <Route path="/"      element={<RunPage />}   />
              <Route path="/leads" element={<LeadsPage />} />
              <Route path="/stats" element={<StatsPage />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  )
}
