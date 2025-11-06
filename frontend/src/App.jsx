import './App.css'
import Chat from './components/Chat'

function App() {
  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <div>
            <div className="title">RAG Chat</div>
            <div className="subtitle">Upload PDFs and ask questions — local RAG</div>
          </div>
        </header>

        <main className="body">
          <Chat />
        </main>
      </div>
    </div>
  )
}

export default App
