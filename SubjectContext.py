
import uuid

class SubjectContext:
    def __init__(self, applicant_name, subject_id = None):
        if (subject_id != None):
            self.id = subject_id
        else:
            self.id = str(uuid.uuid4())
        self.applicant_name = applicant_name
        # Initialize self.id to a UUID
        self.company_name = None
        self.job_title = None
        self.job_desc = None
