import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

class RAGEngine:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        # Using Ollama for embeddings
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.vector_store = None
        self._load_vector_store()

    def _load_vector_store(self):
        if os.path.exists(self.persist_directory):
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            self.vector_store = None

    def add_documents(self, file_paths):
        documents = []
        for file_path in file_paths:
            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            else:
                loader = TextLoader(file_path, encoding='utf-8')
            documents.extend(loader.load())

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(documents)

        if self.vector_store is None:
            self.vector_store = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
        else:
            self.vector_store.add_documents(splits)
        
        return len(splits)

    def query(self, question, k=3):
        if self.vector_store is None:
            return []
        
        results = self.vector_store.similarity_search(question, k=k)
        return [doc.page_content for doc in results]

    def clear_database(self):
        if self.vector_store:
            import shutil
            import gc
            # Close the vector store if it has a persist or client
            self.vector_store = None
            # Force garbage collection to release file handles
            gc.collect()
            
            if os.path.exists(self.persist_directory):
                try:
                    shutil.rmtree(self.persist_directory)
                    return True
                except Exception as e:
                    print(f"Error clearing database: {e}")
                    return False
        return False

    def has_knowledge(self):
        return self.vector_store is not None

    def get_uploaded_files(self):
        if not self.vector_store:
            return {}
        try:
            data = self.vector_store.get()
            if "metadatas" in data and data["metadatas"]:
                sources = {}
                for meta in data["metadatas"]:
                    if meta and "source" in meta:
                        basename = os.path.basename(meta["source"])
                        sources[basename] = meta["source"]
                return sources
        except Exception as e:
            print(f"Error getting sources: {e}")
        return {}

    def delete_file(self, source_path):
        if self.vector_store:
            try:
                data = self.vector_store.get(where={"source": source_path})
                if data and "ids" in data and data["ids"]:
                    self.vector_store.delete(ids=data["ids"])
                    return True
            except Exception as e:
                print(f"Error deleting file {source_path}: {e}")
        return False
