import os
import requests
import app.SubjectContext as SubjectContext

import cli_constants

class CareerAgentSDK:

  def __init__(self, career_agent_url = "http://localhost:8080"):
    self.career_agent_url = career_agent_url

  def ask_conversational_question(self, subject_id: str, userInput: str) -> str:
    response = requests.post(self.career_agent_url + "/chat", data = {'subject_id': subject_id, 'message_text': userInput})
    if response.status_code != 200:
      raise Exception("Failed to get response from server")
    return response.text
  
  def get_chat_history(self, subject_id: str):
    # TODO: Implement this
    return []

# END OF CLASS CareerAgentSDK ====================================================================================================

class WebCLI:

  def __init__(self):
    self.GENERATED_DOCS_FOLDER = getattr(cli_constants, "GENERATED_DOCS_FOLDER", "~/Documents/GeneratedCoverLetters")
    # self.svc = CareerAgentService.CareerAgentService()
    self.sdk = CareerAgentSDK()

  # ====================================================================================================

  def printQuestionPrompt(self, subject_context: SubjectContext):
    print("\n=====================================================\n" +
          "Ask a question about " + subject_context.applicant_name + " or 'Help'\n" +
          "=====================================================\n")

  # ====================================================================================================

  def create_pdf(self, text: str, subject_ctx: SubjectContext, document_type):
    output_folder = self.GENERATED_DOCS_FOLDER
    #Generate a PDF of the cover letter and save to a file named with the company name and job title
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 5, text)
    # write the pdf to the output folder
    output_folder = os.path.expanduser(output_folder)
    if not os.path.exists(output_folder):
      os.makedirs(output_folder)
    output_filename = output_folder + "/" + subject_ctx.company_name + "_" + subject_ctx.job_title + "_" + document_type + ".pdf"
    pdf.output(output_filename)
    print("Saved cover letter to " + output_filename + "\n")

  # ====================================================================================================

  def set_job_description(self, subject_id: str):
    # Read multiple lines of input from the user until they enter a line with only the word "END"
    print("\nEnter the job description. Enter END on a new line when you are done.")
    lines = []
    while True:
      line = input()
      if line == "END":
        break
      lines.append(line)

    job_desc = "\n".join(lines)
    job_title = input("Enter the job title: ")
    company_name = input("Enter the company name: ")

    subject_context = self.svc.get_subject_context(subject_id)
    subject_context.job_desc = job_desc
    subject_context.job_title = job_title
    subject_context.company_name = company_name
    self.svc.save_subject_context(subject_context)

  def start(self):
    
    subject_context = SubjectContext.SubjectContext("Alex Worden", "AlexWorden");

    while True:
      # Catch any exceptions and print them
      try:
        self.printQuestionPrompt(subject_context)
        userInput = input("Q: ")
        if userInput in ['q', 'Q', 'Quit']:
          break
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
        else:
          print("\n... Generating answer ...\n")
          answer = self.sdk.ask_conversational_question(subject_context.id, userInput)
          print(answer + "\n")
      except Exception as e:
        print(e)
        continue
      # END OF TRY/CATCH BLOCK
    # END OF WHILE LOOP
  # END OF CLASS ResumeBuilder ====================================================================================================

WebCLI().start()
