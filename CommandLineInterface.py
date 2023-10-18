import os
import app.SubjectContext as SubjectContext
import app.CareerAgentService as CareerAgentService

import cli_constants

class CommandLineInterface:

  def __init__(self):
    self.GENERATED_DOCS_FOLDER = getattr(cli_constants, "GENERATED_DOCS_FOLDER", "~/Documents/GeneratedCoverLetters")
    self.svc = CareerAgentService.CareerAgentService()

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
    
    subject_context = self.svc.get_subject_context("AlexWorden");
    # Print a summary of the companies that the subject has worked for
    # companies_worked_for = svc.query_embedded_context("List all of the companies that subject has worked for in a bullet list in reverse chronological order with start and end dates")
    # print(user_context.applicant_name + " has worked for the following companies:\n" + companies_worked_for + "\n")

    while True:
      self.printQuestionPrompt(subject_context)
      userInput = input("Q: ")
      if userInput in ['q', 'Q', 'Quit']:
        break
      elif userInput in ['JD']:
        self.set_job_description(subject_context.id)
      elif userInput in ['R']:
        # If company_name and job_title are not set, ask the user to set them
        if (subject_context.company_name == None or subject_context.job_title == None):
          print("Job Description has not been set. Use the 'JD' command to set the job description.")
          continue
        print("Generating resume for " + subject_context.applicant_name + " for the position of " + subject_context.job_title + " at " + subject_context.company_name + "...\n")
        resume = self.svc.generate_resume(subject_context.id)
        print(resume + "\n")
        self.create_pdf(resume, subject_context, "resume")
      elif userInput in ['CL']:
        # If company_name and job_title are not set, ask the user to set them
        if (subject_context.company_name == None or subject_context.job_title == None):
          print("Job Description has not been set. Use the 'JD' command to set the job description.")
          continue
        print("Generating cover letter for " + subject_context.applicant_name + " for the position of " + subject_context.job_title + " at " + subject_context.company_name + "...\n")
        cover_letter = self.svc.generate_cover_letter(subject_context.id)
        print(cover_letter + "\n")
        self.create_pdf(cover_letter, subject_context, "coverletter")
      elif userInput in ['Refresh'] :
        self.svc.initialize_subject(subject_context.id, True)
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
        print(self.svc.get_chat_history(subject_context.id))
      else:
        print("\n... Generating answer ...\n")
        answer = self.svc.ask_conversational_question(subject_context.id, userInput)
        print(answer + "\n")

  # END OF CLASS ResumeBuilder ====================================================================================================

CommandLineInterface().start()
