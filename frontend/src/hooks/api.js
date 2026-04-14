import axios from 'axios'

// Localhost pe test karte waqt ye URL use hoga
// Production (Railway) pe aap yahan apna Railway URL dalenge
const API_BASE = import.meta.env.VITE_API_URL || 'https://lead-generator-agent-1.onrender.com'

const client = axios.create({
  baseURL: API_BASE
})

export const api = {
  // Agent start karo
  run: async (data) => {
    const res = await client.post('/run-agent', data)
    return res.data
  },

  // Job status check karo
  job: async (jobId) => {
    const res = await client.get(`/job/${jobId}`)
    return res.data
  },

  // Leads list fetch karo
  leads: async () => {
    const res = await client.get('/leads')
    return res.data
  },

  // Dashboard stats fetch karo
  stats: async () => {
    const res = await client.get('/stats')
    return res.data
  },

  // Reset data
  reset: async () => {
    const res = await client.delete('/leads/reset')
    return res.data
  },

  // WhatsApp Outreach
  send: async () => {
    const res = await client.post('/send')
    return res.data
  }
}
