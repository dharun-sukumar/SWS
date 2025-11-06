import { useState, useRef } from 'react'
import './chat.css'

function Chat() {
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [files, setFiles] = useState([])
  const fileRef = useRef()

  const send = async () => {
    if (!text.trim()) return
    const userMsg = { id: Date.now(), role: 'user', text: text.trim() }
    setMessages((s) => [...s, userMsg])
    setText('')
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ query: userMsg.text }),
      })
      const data = await res.json()
      const botMsg = { id: Date.now() + 1, role: 'bot', text: data.answer || 'No answer received' }
      setMessages((s) => [...s, botMsg])
    } catch (e) {
      const errMsg = { id: Date.now() + 2, role: 'bot', text: 'Error contacting server' }
      setMessages((s) => [...s, errMsg])
    } finally {
      setLoading(false)
    }
  }

  const upload = async (file) => {
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: fd,
      })
      const data = await res.json()
      if (data.message) {
        setFiles((f) => [...f, { name: file.name, uploadedAt: new Date().toLocaleString() }])
      } else {
        alert('Upload failed: ' + (data.error || 'Unknown error'))
      }
    } catch (e) {
      console.error('Upload failed:', e)
      alert('Error uploading file')
    }
  }

  const onFileChange = (e) => {
    const file = e.target.files[0]
    if (file) upload(file)
  }

  const onDrop = (e) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f) upload(f)
  }

  return (
    <div className="chatContainer">
      <section className="chat">
        <div className="messages" id="messages">
          {messages.map((m) => (
            <div key={m.id} className={`msgRow ${m.role}`}>
              <div className={`msg ${m.role}`}>{m.text}</div>
              <div className="meta muted">
                {m.role} • {new Date(m.id).toLocaleTimeString()}
              </div>
            </div>
          ))}
          {loading && (
            <div className="msgRow bot">
              <div className="msg bot">Thinking…</div>
            </div>
          )}
        </div>

        <div className="composer">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Ask a question about your uploaded PDFs..."
          />
          <button className="btn primary" onClick={send} disabled={loading}>
            Send
          </button>
        </div>
      </section>

      <aside className="upload">
        <div
          className="drop"
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
        >
          <div className="hint">Drag & drop PDF here, or</div>
          <input
            ref={fileRef}
            type="file"
            accept="application/pdf"
            style={{ display: 'none' }}
            onChange={onFileChange}
          />
          <button
            className="btn ghost"
            onClick={() => fileRef.current && fileRef.current.click()}
          >
            Select PDF
          </button>
        </div>

        <div className="files">
          {files.length === 0 ? (
            <div className="hint">No files uploaded</div>
          ) : (
            files.map((f, i) => (
              <div key={i} className="fileItem">
                <div>
                  <div className="fileName">{f.name}</div>
                  <div className="fileMeta">{f.uploadedAt}</div>
                </div>
                <div className="kbd">Uploaded</div>
              </div>
            ))
          )}
        </div>
      </aside>
    </div>
  )
}

export default Chat
