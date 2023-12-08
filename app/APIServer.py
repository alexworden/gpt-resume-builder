from flask import Flask, request
from flask_cors import CORS, cross_origin
import logging
import CareerAgentService as CareerAgentService

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# TODO: Figure out how to access pre-initialized CareerAgentService instances for performance or determine if they can be initialized on demand for each subject_id request
career_agent = CareerAgentService.CareerAgentService()

# API for accepting a chat message related to a subject_id and providing a chat question in the body of the request
@app.route("/chat", methods=['POST'])
@cross_origin()
def chat():
  request_data = request.get_json()
  app.logger.debug('Received request: "%s"', request_data)
  subject_id = request_data['subject_id']
  message_text = request_data['message_text']
  logging.debug("Received chat request for subject_id: " + subject_id + " with message_text: " + message_text)

  msg_response = career_agent.ask_simple_with_context(subject_id, message_text)
  return msg_response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
