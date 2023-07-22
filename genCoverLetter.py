import os
import sys
import shutil

import openai
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.memory import ConversationBufferMemory
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
PERSIST_FOLDER = PERSONAL_DOCS_FOLDER + "_persist"
# GPT_MODEL = "gpt-3.5-turbo"
GPT_MODEL = "gpt-3.5-turbo-16k"
GENERATED_DOCS_FOLDER = getattr(constants, "GENERATED_DOCS_FOLDER", "~/Documents/GeneratedCoverLetters")

chat_history = []


def ask_conversational_question(question): 
    answer = chain({"question": question, "chat_history": chat_history})['answer']
    chat_history.append((question, answer))
    return answer

def get_answer(question):
  return index.query(question)

def build_embedding_chain(persist_folder, personal_docs_folder, gpt_model=GPT_MODEL, clean=False):
  
  if (clean):
    print("Rebuilding the personal docs index...")
    # if the persist_folder exists, delete it
    if os.path.exists(persist_folder):
      shutil.rmtree(persist_folder)
    # create a new index
    loader = DirectoryLoader(personal_docs_folder)
    index = VectorstoreIndexCreator(
      text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100), vectorstore_kwargs={"persist_directory":PERSIST_FOLDER}).from_loaders([loader])
  else:
    print("Reusing vectorstore from " + PERSIST_FOLDER + " directory...\n")
    vectorstore = Chroma(persist_directory=PERSIST_FOLDER, embedding_function=OpenAIEmbeddings())
    index = VectorStoreIndexWrapper(vectorstore=vectorstore)
  
  chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model=GPT_MODEL),
    retriever=index.vectorstore.as_retriever(search_kwargs={"k": 10}),
  )

  return (index, chain)

def generate_cover_letter(applicant_name, output_folder=GENERATED_DOCS_FOLDER):
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

    most_relevant_skill = get_answer("Summarize Alex Worden's single most relevant experience to the most important requirement in following job description below using one or two words to state the type of experience. \n" + job_desc)

    print("\nAlex Worden's most relevant experience to the most important requirement in the job description is: " + most_relevant_skill + "\n")

    query = "Write a job application cover letter for me, " + applicant_name + ". The cover letter is for the role of " + job_title + " at company '" + company_name + "' for the following job description '" + job_desc + "'. The cover letter should be addressed to the hiring manager. The cover letter should be no more than 400 words. The cover letter should be written in a polite, friendly, and informal tone that is genuine and enthusiastic. Start the letter with: \"I'm excited to apply for the role of " + job_title + " at " + company_name + ". I believe the following skills and experience I have are a good fit for the role:\". Provide only 3 to 5 bullet points that highlight my skills and experience that are a good match for the requirements stated in the job description. Do not directly quote the phrases used in the job description, but instead, quote my relevant skills and experience. Add a genuine, but not overstated sentence about why the company mission is important to me. Don't elaborate too much. Add a short closing paragraph thanking the hiring manager for their time and consideration."

    print("\n\n... Generating cover letter ...\n ")
    cover_letter = ask_conversational_question(query)
    print("Cover Letter:\n\n" + cover_letter + "\n")
    print("\n========================\n")

    #Generate a PDF of the cover letter and save to a file named with the company name and job title
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 5, cover_letter)
    # write the pdf to the output folder
    if not os.path.exists(output_folder):
      os.makedirs(output_folder)
    pdf.output(output_folder + "\\" + company_name + "_" + job_title + ".pdf")
    
    # ask the user if they want to generate another cover letter
    while True:
      answer = input("Generate another cover letter? (y/n): ")
      if answer == "n":
        return
      elif answer == "y":
        break
      else:
        print("Invalid response. Please enter y or n.")


# ================== START OF MAIN PROGRAM ==================

# if os.path.exists(PERSIST_FOLDER): 
#   chain = build_embedding_chain(PERSIST_FOLDER, PERSONAL_DOCS_FOLDER, clean=False)
# else:
(index, chain) = build_embedding_chain(PERSIST_FOLDER, PERSONAL_DOCS_FOLDER, clean=True)

# result = chain({"question": "Tell me the name of the person that the resume is about? Reply with only the name and use the full name if you have that information, otherwise reply with the token UNKNOWN", "chat_history": chat_history})
# applicant_name = result['answer']

applicant_name = get_answer("What is the name of the person that the resume is about? Reply with only the name and use the full name if you have that information, otherwise reply with the token UNKNOWN")

companies_worked_for = get_answer("List all of the companies that " + applicant_name + " has worked for in a bullet list in reverse chronological order with start and end dates")

print(applicant_name + " has worked for the following companies:\n" + companies_worked_for + "\n")

while True:
  print("=====================================================\n" +
        "Ask a question about " + applicant_name + ".\n" + 
        "Enter 'q' to exit.\n" +
        "Enter 'Gen Cover Letter' to generate a cover letter.\n" +
        "=====================================================\n")
  userInput = input("Q: ")
  if userInput in ['quit', 'q']:
    break
  elif userInput == "Gen Cover Letter":
    generate_cover_letter(applicant_name="Alex Worden")
    print("Ask more questions about the skills and experience of " + applicant_name + ". Enter 'quit' to exit.\n")
  elif userInput == "Refresh":
    index = build_embedding_chain(PERSIST_FOLDER, PERSONAL_DOCS_FOLDER)
  else:
    userInput = "answer the following question '" + userInput + "' in relation to " + applicant_name + ". Assume that references to 'I' and 'me' refer to " + applicant_name + ". You answers should substitute the personal pronouns 'I' and 'me' with the name " + applicant_name + "."
    print("\n... Generating answer ...\n")
    answer = ask_conversational_question(userInput)
    print(answer + "\n")

    #chat_history.append((userInput, result['answer']))

