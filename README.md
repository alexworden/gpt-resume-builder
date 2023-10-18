Career Agent App
================

The app is (currently) composed of the following:  

 * /app - A web app API to provide http access to the CareerAgentService 
 * CareerAgentService - A class encapsulating the logic to manage the embeddings and LLM chat for a subject (needs renaming since it's not a service as such)
 * CommandLineInterface.py - a command line interface that will allow you to chat with the CareerAgentService. TODO: this should interact with the webapp interface
 * React WebApp - UI to be hosed and allow access to the /app web service. 

#Building

The project is being containerized in Docker

Legacy (?): Set the python interpreter in your editor to conda (install it if necessary)

pip install -r requirements.txt
python CommandLineInterface.py

#Deploying Locally

See: https://kubernetes.io/blog/2019/07/23/get-started-with-kubernetes-using-python/

Create docker image: 

```
cd app
docker build -f Dockerfile -t career-agent:latest .
docker image ls
```

Running in Docker
```
docker run -p 8001:8000 career-agent
```
Running in Kubernetes Locally
```

```
