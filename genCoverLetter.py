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

import constants

os.environ["OPENAI_API_KEY"] = constants.APIKEY

# Enable to save to disk & reuse the model (for repeated queries on the same data)
PERSONAL_DOCS_FOLDER = "personal_docs"
PERSIST_FOLDER = PERSONAL_DOCS_FOLDER + "_persist"
# GPT_MODEL = "gpt-3.5-turbo"
GPT_MODEL = "gpt-3.5-turbo"

def rebuild_embedding_chain(persist_folder, personal_docs_folder, gpt_model=GPT_MODEL):
  print("Rebuilding the personal docs index...")
  # if the persist_folder exists, delete it
  if os.path.exists(persist_folder):
    shutil.rmtree(persist_folder)
  # create a new index
  loader = DirectoryLoader(personal_docs_folder)
  index = VectorstoreIndexCreator(vectorstore_kwargs={"persist_directory":PERSIST_FOLDER}).from_loaders([loader])
  chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model=gpt_model),
    retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
  )
  return chain

def generate_cover_letter():
  while True:
    chat_history = []
    company_name = input("Enter the company name: ")
    job_title = input("Enter the job title: ")
    # Read multiple lines of input from the user until they enter a line with only the word "END"
    print("\nEnter the job description. Enter END on a new line when you are done.")
    lines = []
    while True:
      line = input()
      if line == "END":
        break
      lines.append(line)

    # Join the lines together into a String with a newline character between each line
    job_desc = "\n".join(lines)

    query = "Write a job application cover letter for the person who's resume and personal details are known to you. The cover letter is for the role of " + job_title + " at company '" + company_name + "' for the following job description '" + job_desc + "'. The cover letter should be addressed to the hiring manager. The cover letter should be no more than 300 words. The cover letter should be written in a polite, friendly, and informal tone that is short, enthusiastic. Provide 3 to 5 bullet points to highlight where my skills and experience are a good for the job description, prioritizing the must have skills and experience mentioned in the above job description. Starting the letter with: \"I'm' excited to apply for the role of " + job_title + " at " + company_name + ". I believe my skills and experience are a good fit for the role:\". Add a sentence about why the company mission is important to me. Don't elaborate beyond the bullet points. Add a short closing paragraph thanking the hiring manager for their time and consideration. Sign off using the full name from the resume context"

    print("\n\n... Generating cover letter ...\n\n")
    result = chain({"question": query, "chat_history": chat_history})
    print("Cover Letter:\n")
    print(result['answer'])
    print("\n========================\n")

    #Generate a PDF of the cover letter and save to a file named with the company name and job title
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 5, result['answer'])
    pdf.output(company_name + "_" + job_title + ".pdf")

    #ask the user if they want to generate another cover letter
    # if they say no, exit the program
    # if they say yes, repeat the process
    # if they enter an invalid response, ask them again
    while True:
      answer = input("Generate another cover letter? (y/n): ")
      if answer == "n":
        return
      elif answer == "y":
        break
      else:
        print("Invalid response. Please enter y or n.")


# ================== START OF MAIN PROGRAM ==================
# If PERSIST is enabled and the persist directory exists, reuse the index
if os.path.exists(PERSIST_FOLDER): 
  print("Reusing vectorstore from " + PERSIST_FOLDER + " directory...\n")
  vectorstore = Chroma(persist_directory=PERSIST_FOLDER, embedding_function=OpenAIEmbeddings())
  index = VectorStoreIndexWrapper(vectorstore=vectorstore)
  chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model=GPT_MODEL),
    retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
  )
else:
  chain = rebuild_embedding_chain(PERSIST_FOLDER, PERSONAL_DOCS_FOLDER)

chat_history = []

print("Ask questions about your skills and experience from documents in the " + PERSIST_FOLDER + " folder. Enter 'quit' to exit.\n")
while True:
  query = input(": ")
  if query in ['quit', 'q', 'exit']:
    break
  elif query == "Gen Cover Letter":
    generate_cover_letter()
  elif query == "Refresh":
    chain = rebuild_embedding_chain(PERSIST_FOLDER, PERSONAL_DOCS_FOLDER)
  else:
    result = chain({"question": query, "chat_history": chat_history})
    print(result['answer'])

    chat_history.append((query, result['answer']))
    query = None

# BEGIN: 9f8c6549bwf9

# END: 9f8c6549bwf9
    
