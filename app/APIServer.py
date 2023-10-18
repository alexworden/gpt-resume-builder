from flask import Flask
from flask import Flask, request
import CareerAgentService as CareerAgentService

app = Flask(__name__)

# TODO: Figure out how to access pre-initialized CareerAgentService instances for performance or determine if they can be initialized on demand for each subject_id request
career_agent = CareerAgentService.CareerAgentService()

# API for accepting a chat message related to a subject_id and providing a chat question in the body of the request
@app.route("/chat", methods=['POST'])
def chat():
  subject_id = request.form['subject_id']
  message_text = request.form['message_text']

  msg_response = career_agent.ask_simple_with_context(subject_id, message_text)
  return msg_response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
