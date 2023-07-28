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

class ResumeBuilder:

  def __init__(self):
    # Enable to save to disk & reuse the model (for repeated queries on the same data)
    self.PERSONAL_DOCS_FOLDER = "personal_docs"
    self.PERSIST_FOLDER = self.PERSONAL_DOCS_FOLDER + "_persist"
    # GPT_MODEL = "gpt-3.5-turbo-16k"
    self.GPT_MODEL = "gpt-3.5-turbo"
    self.GENERATED_DOCS_FOLDER = getattr(constants, "GENERATED_DOCS_FOLDER", "~/Documents/GeneratedCoverLetters")

    self.chat_history = []
    self.build_embedding_chain(self.PERSIST_FOLDER, self.PERSONAL_DOCS_FOLDER, clean=False)
  
  # ====================================================================================================

  def ask_conversational_question(self, question, clear_chat_history=False): 
      # print("\n=========================================\nAsking conversational question:\n" + 
      #       question + "\n=========================================\n")
      if (clear_chat_history):
        self.chat_history = []
      
      answer = self.chain({"question": question, "chat_history": self.chat_history})['answer']
      self.chat_history.append((question, answer))
      return answer

  # ====================================================================================================

  def get_answer(self, question):
    return self.index.query(question)

  # ====================================================================================================

  def build_embedding_chain(self, persist_folder, personal_docs_folder, clean=False):

    if (clean):
      print("Rebuilding the personal docs index...")
      # if the persist_folder exists, delete it
      if os.path.exists(persist_folder):
        shutil.rmtree(persist_folder)
      # create a new index
      loader = DirectoryLoader(personal_docs_folder)
      self.index = VectorstoreIndexCreator(
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100), vectorstore_kwargs={"persist_directory":self.PERSIST_FOLDER}).from_loaders([loader])
    else:
      print("Reusing vectorstore from " + self.PERSIST_FOLDER + " directory...\n")
      vectorstore = Chroma(persist_directory=self.PERSIST_FOLDER, embedding_function=OpenAIEmbeddings())
      self.index = VectorStoreIndexWrapper(vectorstore=vectorstore)
    
    self.chain = ConversationalRetrievalChain.from_llm(
      llm=ChatOpenAI(model=self.GPT_MODEL),
      retriever=self.index.vectorstore.as_retriever(search_kwargs={"k": 10}),
    )

  # ====================================================================================================

  def set_job_description(self, applicant_name):
    self.chat_history = []
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

    '''
    # Use get_answer() to get the job title and company name from the job description
    job_title = self.get_answer("State only the job title for the following job description?\n" + job_desc)
    company_name = self.get_answer("State the company name for the following job description?\n" + job_desc)

    # Ask the user to confirm the job title and company name
    print("\nIs the following job title correct? " + job_title)
    answer = input("Enter new job title or return to accept: ")
    if answer != None:
      job_title = answer
    
    print("\nIs the following company name correct? " + company_name)
    answer = input("Enter company name or return to accept: ")
    if answer != None:
      company_name = answer
    '''
    job_title = input("Enter the job title: ")
    company_name = input("Enter the company name: ")

    return (company_name, job_title, job_desc)

  def get_job_requirements(self):
    if (self.job_desc == None):
      print("Job description has not been set. Use the 'JD' command to set the job description.")
      return
    
    top_requirements = self.ask_conversational_question("Provide a bullet list of the 10 most important requirements for the following job description?\n" + self.job_desc)
    print("\nTop Job Requirements:\n" + top_requirements)

    most_relevant_skills = self.ask_conversational_question("Given the following job requirements: \n" 
                                                      + top_requirements + "\n\nFor each requirement, quote the requirement in the order given, then provide a first person quote from " 
                                                      + self.applicant_name + " on how their skills and/or experience meet the requirement. For example, if the requirement is 'Must have a degree in Computer Science', then the answer should be 'I have a degree in Computer Science from the University of Toronto'.Provide only the answers in a bullet list in the same order as the requirements and nothing else.")
    
    print("\n" + self.applicant_name + "'s most relevant experience to the most important requirement in the job description are:\n\n" + most_relevant_skills + "\n")

    return (top_requirements, most_relevant_skills)

  # ====================================================================================================

  def generate_cover_letter(self, applicant_name, company_name, job_title, job_desc, output_folder=None):
    output_folder = output_folder or self.GENERATED_DOCS_FOLDER

    query = "Write a job application cover letter from " + applicant_name + " for the role of '" + job_title + "' at company '" + company_name + "' for the job description given below. The cover letter should be addressed to the hiring manager. The cover letter should be no more than 400 words. The cover letter should be written in a polite, friendly, and informal tone that is genuine and enthusiastic. Start the letter with: \"I'm excited to apply for the role of " + job_title + " at " + company_name + ". I believe the following skills and experience I have are a good fit for the role:\". Provide only 3 to 5 bullet points that highlight my skills and experience that are a good match for the requirements stated in the job description. Do not directly quote the phrases used in the job description, but instead, quote my relevant skills and experience. Add a genuine, but not overstated sentence about why the company mission is important to me. Don't elaborate too much. Add a short closing paragraph thanking the hiring manager for their time and consideration. The job description is as follows: \n\n" + job_desc + "\n\n"

    print("\n\n... Generating cover letter ...\n ")
    cover_letter = self.ask_conversational_question(query, True)
    print("Cover Letter:\n\n" + cover_letter + "\n")
    print("\n========================\n")

    #Generate a PDF of the cover letter and save to a file named with the company name and job title
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 5, cover_letter)
    # write the pdf to the output folder
    output_folder = os.path.expanduser(output_folder)
    if not os.path.exists(output_folder):
      os.makedirs(output_folder)
    output_filename = output_folder + "/" + company_name + "_" + job_title + ".pdf"
    pdf.output(output_filename)
    print("Saved cover letter to " + output_filename + "\n")


  # ====================================================================================================

  def start(self):

    applicant_name = self.get_answer("What is the name of the person that the resume is about? Reply with only the name and use the full name if you have that information, otherwise reply with the token UNKNOWN")

    companies_worked_for = self.get_answer("List all of the companies that " + applicant_name + " has worked for in a bullet list in reverse chronological order with start and end dates")

    print(applicant_name + " has worked for the following companies:\n" + companies_worked_for + "\n")

    while True:
      print("\n=====================================================\n" +
            "Ask a question about " + applicant_name + ". Enter 'Q = Quit', 'CL = Gen Cover Letter' or 'JD = Set Job Description'" +
            "\n=====================================================\n")
      userInput = input("Q: ")
      if userInput in ['Q', 'Quit']:
        break
      elif userInput in ['JD', 'Set Job Description']:
        (company_name, job_title, job_desc) = self.set_job_description(applicant_name=applicant_name)
      elif userInput in ['CL', 'Gen Cover Letter']:
        self.generate_cover_letter(applicant_name=applicant_name, company_name=company_name, job_title=job_title, job_desc=job_desc)
        print("Ask more questions about the skills and experience of " + applicant_name + ". Enter 'quit' to exit.\n")
      elif userInput in ['R', 'Refresh'] :
        index = self.build_embedding_chain(self.PERSIST_FOLDER, self.PERSONAL_DOCS_FOLDER, clean=True)
        chat_history = []
      else:
        userInput = "answer the following question '" + userInput + "' in relation to " + applicant_name + ". Assume that references to 'I' and 'me' refer to " + applicant_name + ". You answers should substitute the personal pronouns 'I' and 'me' with the name " + applicant_name + "."
        print("\n... Generating answer ...\n")
        answer = self.ask_conversational_question(userInput)
        print(answer + "\n")

  # END OF CLASS ResumeBuilder ====================================================================================================

ResumeBuilder().start()
