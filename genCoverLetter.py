import os
import sys
import shutil
import json

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

class UserContext:
    def __init__(self, applicant_name):
        self.applicant_name = applicant_name
        self.company_name = None
        self.job_title = None
        self.job_desc = None

class ResumeBuilder:

  def __init__(self):
    # Enable to save to disk & reuse the model (for repeated queries on the same data)
    self.PERSONAL_DOCS_FOLDER = "personal_docs"
    self.PERSIST_FOLDER = self.PERSONAL_DOCS_FOLDER + "_persist"
    self.GPT_4K_MODEL = "gpt-3.5-turbo"
    self.GPT_16K_MODEL = "gpt-3.5-turbo-16k"
    self.GENERATED_DOCS_FOLDER = getattr(constants, "GENERATED_DOCS_FOLDER", "~/Documents/GeneratedCoverLetters")

    self.chat_history = []
    self.build_embedding_chain(self.PERSIST_FOLDER, self.PERSONAL_DOCS_FOLDER, clean=False)
  
  # ====================================================================================================

  def ask_conversational_question(self, question, clear_chat_history=False): 
    if (clear_chat_history):
      self.chat_history = []
    
    # full_prompt = "Question: " + question + "\nChat History: " + str(self.chat_history)
    # print("Sending prompt to OpenAI: " + full_prompt)
    answer = self.chain_small({"question": question, "chat_history": self.chat_history})['answer']
    self.chat_history.append((question, answer))
    return answer

  # ====================================================================================================

  def ask_simple_with_context(self, question):
    return self.chain_small({"question": question, "chat_history": []})['answer']

  # ====================================================================================================

  def ask_complex_with_context(self, question):   
    return self.chain_big({"question": question, "chat_history": []})['answer']

  # ====================================================================================================

  def ask_wrt_context(self, question):
    return self.index.query(question)

  # ====================================================================================================
  
  def ask_without_context(self, prompt):
    response = openai.Completion.create(
      model="gpt-3.5-turbo-instruct",
      prompt=prompt,
      temperature=0,
      max_tokens=300
    )
    return response['choices'][0]['text']

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
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0), 
        vectorstore_kwargs={"persist_directory":self.PERSIST_FOLDER}).from_loaders([loader])
    else:
      print("Reusing vectorstore from " + self.PERSIST_FOLDER + " directory...\n")
      vectorstore = Chroma(persist_directory=self.PERSIST_FOLDER, embedding_function=OpenAIEmbeddings())
      self.index = VectorStoreIndexWrapper(vectorstore=vectorstore)
    
    self.chain_small = ConversationalRetrievalChain.from_llm(
      llm=ChatOpenAI(model=self.GPT_4K_MODEL),
      retriever=self.index.vectorstore.as_retriever(search_kwargs={"k": 8}),
      verbose=False,
    )

    self.chain_big = ConversationalRetrievalChain.from_llm(
      llm=ChatOpenAI(model=self.GPT_16K_MODEL),
      retriever=self.index.vectorstore.as_retriever(search_kwargs={"k": 20}),
    )

  # ====================================================================================================

  def set_job_description(self, user_context):
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
    user_context.job_desc = "\n".join(lines) 

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
    user_context.job_title = input("Enter the job title: ")
    user_context.company_name = input("Enter the company name: ")


  # ====================================================================================================

  def get_job_requirements(self, user_context):
    if (user_context.job_desc == None):
      print("Job description has not been set. Use the 'JD' command to set the job description.")
      return

    job_qualification = self.ask_without_context("You are a diligent and smart job applicant. Summarize and prioritize up to 8 qualifications from the following job description, providing your answer in JSON format where each qualification summary is a string in a JSON list.\n\nJob Description:\n" + user_context.job_desc)
    print("\nTop Job Requirements:\n" + job_qualification)

    # Parse the top_requirements as JSON and iterate over the list of job_qualifications
    job_qualification = json.loads(job_qualification)
    most_relevant_skills = []
    for qualification in job_qualification:
      # Create a short paragraph on how the candidate's context meets each job qualification
      candidate_skill = self.ask_wrt_context("You are writing a bullet point in a job cover letter. Your answer must be from a first person perspective. Avoid quoting text from the qualification word-for-word. Write a concise summary sentence that demonstrates how my experiences and skills meet the following job qualification: " + qualification + "\n\n")
      print("\nJob qualification: " + qualification + "\nExperience: " + candidate_skill + "\n\n")
      # Add the candidate_skill to the list of most_relevant_skills
      most_relevant_skills.append(candidate_skill)


    print("\n" + user_context.applicant_name + "'s most relevant experience to the most important requirement in the job description are:\n")
    # Create a bullet list of the most_relevant_skills and append to a string
    skills_list = ""
    for skill in most_relevant_skills:
      skills_list += " * " + skill + "\n"
    
    print("Candidate Skills:\n" + skills_list + "\n")

    cleaned_json_skills = self.ask_complex_with_context("You are an recruitment expert and have been asked to copy-edit the following list of candidate skills to be included in a cover letter. You MUST provide your answer in JSON format where each list item is a string in a JSON list like the following format:\n [\"Item one\", \"Item two\", \"Item three\"]. Remove repeated skills and redundant statements from the input list items and condense each item in the following list without losing valuable Knowledge, Skills, and Abilities (KSA) or soft skills such as such as optimism, kindness, intellectual curiosity, strong work ethic, empathy, and integrity. Prioritise the items, placing the most important first and limit to a maximum of 6 items. Always include the first item as the number of years experience:\n\n" + skills_list)
    print("Cleaned Skills:\n" + cleaned_json_skills + "\n")

    # parse the jscon cleaned_json_skills into a list
    # handle exceptions parsing the json
    try:
      job_skills = json.loads(cleaned_json_skills)
    except: 
      print("Error parsing JSON. Trying to convert to JSON list of strings.")
      cleaned_json_skills = self.ask_without_context("Format the following into a JSON list of strings:\n" + cleaned_json_skills  + "\n")
      try:
        job_skills = json.loads(cleaned_json_skills)
      except:
        print("Unable to create cover letter. Error parsing JSON response from OpenAI: \n" + cleaned_json_skills + "\n")
        return []

    return (job_skills)

  # ====================================================================================================

  def generate_cover_letter(self, user_context, output_folder=None):
    output_folder = output_folder or self.GENERATED_DOCS_FOLDER
    skill_list = self.get_job_requirements(user_context)

    cover_letter = "Thank you for considering my application for the role of " + user_context.job_title + " at " + user_context.company_name + ". I believe the following skills and experience I have are a great fit:\n\n"
    for skill in skill_list:
      cover_letter += " * " + skill + "\n"
    
    mission_alignment = self.ask_complex_with_context("You are a diligent and smart job applicant. Write a very short closing statement in a cover letter to demonstrate how the company mission resonates with your interestes, career aspirations, or passions. Provide your answer by completing the following sentence in less than 25 words: \"I am excited about the opportunity to work at " + user_context.company_name + " because I \".\n\n Base your answer upon the following job description:\n\n" + user_context.job_desc + "\n\n")
    cover_letter += mission_alignment + ".\n\n"

    cover_letter += "Thank you for your time and consideration,\n\n" + user_context.applicant_name + "\n\n"

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
    output_filename = output_folder + "/" + user_context.company_name + "_" + user_context.job_title + ".pdf"
    pdf.output(output_filename)
    print("Saved cover letter to " + output_filename + "\n")


# ====================================================================================================

  def generate_resume(self, user_context, output_folder=None):
    output_folder = output_folder or self.GENERATED_DOCS_FOLDER

    query = "Write a resume for " + user_context.applicant_name + " with sections the following sections: 'Summary' describing " + user_context.applicant_name + "'s overall philosophy and value, 'Summary of Skills and Experience' with a short bullet list of " + user_context.applicant_name + "'s skills and experience that are relvant, 'Work Experience' with an entry for each company " + user_context.applicant_name + " has worked at and a 3-5 item bullet list of " + user_context.applicant_name + "'s relevant accomplishments, and 'Education'. The resume should highlight " + user_context.applicant_name + "'s skills and experience that are relevant to the qualifications outlined in the following job description:\n" + user_context.job_desc + "\n"

    print("\n\n... Generating Resume ...\n ")
    cover_letter = self.ask_generative_question(query)
    print("\n\n" + cover_letter + "\n\n")
    print("===========================================================\n")

    #Generate a PDF of the resume letter and save to a file named with the company name and job title
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 5, cover_letter)
    # write the pdf to the output folder
    output_folder = os.path.expanduser(output_folder)
    if not os.path.exists(output_folder):
      os.makedirs(output_folder)
    output_filename = output_folder + "/Resume of " + user_context.applicant_name + " (" + user_context.company_name + "_" + user_context.job_title + ").pdf"
    pdf.output(output_filename)
    print("Saved resume to " + output_filename + "\n")

  # ====================================================================================================

  def printQuestionPrompt(self, user_context):
    print("\n=====================================================\n" +
          "Ask a question about " + user_context.applicant_name + " or 'Help'\n" +
          "=====================================================\n")

  # ====================================================================================================

  def start(self):
    user_context = UserContext(applicant_name = self.ask_wrt_context("What is the name of the person that the resume is about? Reply with only the name and use the full name if you have that information, otherwise reply with the token UNKNOWN"))
    
    # Print a summary of the companies that the subject has worked for
    # companies_worked_for = self.query_embedded_context("List all of the companies that " + applicant_name + " has worked for in a bullet list in reverse chronological order with start and end dates")
    # print(applicant_name + " has worked for the following companies:\n" + companies_worked_for + "\n")

    while True:
      self.printQuestionPrompt(user_context)
      userInput = input("Q: ")
      if userInput in ['q', 'Q', 'Quit']:
        break
      elif userInput in ['JD']:
        self.set_job_description(user_context)
      elif userInput in ['R']:
        # If company_name and job_title are not set, ask the user to set them
        if (user_context.company_name == None or user_context.job_title == None):
          print("Job Description has not been set. Use the 'JD' command to set the job description.")
          continue
        self.generate_resume(user_context)
      elif userInput in ['CL']:
        # If company_name and job_title are not set, ask the user to set them
        if (user_context.company_name == None or user_context.job_title == None):
          print("Job Description has not been set. Use the 'JD' command to set the job description.")
          continue
        self.generate_cover_letter(user_context)
      elif userInput in ['Refresh'] :
        index = self.build_embedding_chain(self.PERSIST_FOLDER, self.PERSONAL_DOCS_FOLDER, clean=True)
        chat_history = []
      elif userInput in ['Help']:
        print("\n=====================================================\n" +
              "Commands:\n" +
              "JD = Set Job Description\n" +
              "R = Generate Resume\n"
              "CL = Generate Cover Letter\n" +
              "Refresh = Refresh Documents\n" +
              "Q = Quit\n" +
              "=====================================================\n")
      elif userInput in ['']:
        continue
      elif userInput in ['Chat History']:
        print(self.chat_history)
      else:
        print("\n... Generating answer ...\n")
        answer = self.ask_conversational_question("You are a smart,friendly, and truthful job candidate looking for your next opportunity. ALWAYS provide your answer in the first person. Answer the following question concisely, only referencing the experiences described in the context: " + userInput)
        print(answer + "\n")

  # END OF CLASS ResumeBuilder ====================================================================================================

ResumeBuilder().start()
