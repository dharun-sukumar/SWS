import os
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

pdf_folder = "./data"
db_path = "./chroma_db"

embeddings = OllamaEmbeddings(model="mxbai-embed-large")
llm = ChatOllama(model="llama3.2", temperature=0.2)

if not os.path.exists(db_path):
    all_docs = []
    for file in os.listdir(pdf_folder):
        if file.endswith(".pdf"):
            path = os.path.join(pdf_folder, file)
            loader = PyPDFLoader(path)
            all_docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    split_docs = splitter.split_documents(all_docs)

    vectorstore = Chroma.from_documents(split_docs, embedding=embeddings, persist_directory=db_path)
else:
    vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

def ask_question(question):
    print(f"\nQuestion: {question}")
    try:
        related_docs = retriever.invoke(question)
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
        print(f"Answer: {answer.content}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Ready!")
    while True:
        q = input("\nYour question: ").strip()
        if q.lower() in ["quit", "exit", "q"]:
            break
        if q:
            ask_question(q)
