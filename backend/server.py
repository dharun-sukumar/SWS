import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_groq import ChatGroq 
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader as PDFLoader

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pdf_folder = "./data"
db_path = "./chroma_db"

os.makedirs(pdf_folder, exist_ok=True)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.1-8b-instant", temperature=0.2)
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

# Build or load vectorstore
if not os.path.exists(db_path):
    all_docs = []
    for file in os.listdir(pdf_folder):
        if file.endswith(".pdf"):
            path = os.path.join(pdf_folder, file)
            loader = PDFLoader(path)
            all_docs.extend(loader.load())

    split_docs = splitter.split_documents(all_docs)

    vectorstore = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=db_path
    )
else:
    vectorstore = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings
    )

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

class Question(BaseModel):
    query: str

@app.post("/ask")
async def ask_question(item: Question):
    try:
        question = item.query
        related_docs = retriever.invoke(question)

        if not related_docs:
            return {"question": question, "answer": "Not enough context. Try uploading relevant documents."}

        context = "\n\n".join(doc.page_content for doc in related_docs)
        prompt = f"""
        You are a helpful assistant.
        Use the information below to answer the question.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
        answer = llm.invoke(prompt)
        return {"question": question, "answer": answer.content.strip()}
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(pdf_folder, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        loader = PDFLoader(file_path)
        docs = loader.load()
        split_docs = splitter.split_documents(docs)
        vectorstore.add_documents(split_docs)
        vectorstore.persist()

        return {"message": f"{file.filename} uploaded and added to database successfully."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "RAG API is running. Use POST /ask for queries or POST /upload to upload PDFs."}
