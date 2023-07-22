import os
import sys
import shutil

import openai
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

import constants

os.environ["OPENAI_API_KEY"] = constants.APIKEY

# Enable to save to disk & reuse the model (for repeated queries on the same data)
PERSONAL_DOCS_FOLDER = "personal_docs"
PERSIST_FOLDER = PERSONAL_DOCS_FOLDER + "_resume_chat_persist"
# GPT_MODEL = "gpt-3.5-turbo-16k"
GPT_MODEL = "gpt-3.5-turbo"

chat_history = []

def build_embedding_chain(persist_folder, personal_docs_folder, gpt_model=GPT_MODEL, clean=False):
  
  if (clean):
    print("Rebuilding the personal docs index...")
    # if the persist_folder exists, delete it
    if os.path.exists(persist_folder):
      shutil.rmtree(persist_folder)
    # create a new index
    loader = DirectoryLoader(personal_docs_folder)
    index = VectorstoreIndexCreator(
      text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0), 
      vectorstore_kwargs={"persist_directory":PERSIST_FOLDER}).from_loaders([loader])
  else:
    print("Reusing vectorstore from " + PERSIST_FOLDER + " directory...\n")
    vectorstore = Chroma(persist_directory=PERSIST_FOLDER, embedding_function=OpenAIEmbeddings())
    index = VectorStoreIndexWrapper(vectorstore=vectorstore)
  
  chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model=GPT_MODEL),
    retriever=index.vectorstore.as_retriever(search_kwargs={"k": 10}),
  )
  return chain


def ask_question(question): 
    answer = chain({"question": question, "chat_history": chat_history})['answer']
    chat_history.append((question, answer))
    return answer

# ================== START OF MAIN PROGRAM ==================

# If PERSIST is enabled and the persist directory exists, reuse the index
# if os.path.exists(PERSIST_FOLDER): 
#   chain = build_embedding_chain(PERSIST_FOLDER, PERSONAL_DOCS_FOLDER, clean=False)
# else:
chain = build_embedding_chain(PERSIST_FOLDER, PERSONAL_DOCS_FOLDER, clean=True)

applicant_name = ask_question("What is the name of the person that the resume is about? Reply with only the name and use the full name if you have that information, otherwise reply with the token UNKNOWN")
companies_worked_for = ask_question("List all of the companies that " + applicant_name + " has worked for in a bullet list in reverse chronological order with start and end dates")
print(applicant_name + " has worked for the following companies:\n" + companies_worked_for + "\n")

while True:
  print("=====================================================\n" +
        "Ask a question about " + applicant_name + "'s work experience.\n" + 
        "Enter 'q' to exit.\n" +
        "=====================================================\n")
  
  query = input(": ")
  if query in ['quit', 'q', 'exit']:
    break
  elif query == "Refresh":
    chat_history = []
    chain = rebuild_embedding_chain(PERSIST_FOLDER, PERSONAL_DOCS_FOLDER)
  elif query == "Clear":
    chat_history = []
  else:
    print(ask_question(query) + "\n")

