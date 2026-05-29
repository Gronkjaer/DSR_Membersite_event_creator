# DSR Membersite event creator

This repository contains a web application that makes it easier to create repeating events on Membersite. 
The application is intended only for members of DSR (Danske Studenters Roklub).

<br>

## Use the application
The application is deployed on Render, from where you can use the application. See the link below.

https://dsr-membersite-event-creator.onrender.com

<br>

## Code changes
If you want to contribute, you are welcome to update the code yourself. Create a new branch and implement your desired 
feature. Yhen open a pull request to merge into main. Please validate on your own laptop that it works before merging 
into main (preferably with Docker as well). Whenever the main branch is updated, the project is automatically deployed 
on Render.

<br>


## Running locally
To run the application with Python, execute the commands below. This application has been tested with Python 3.10 – 3.13. 
Google Chrome is required.

```bash
pip install -r requirements.txt
python app.py
```

Alternative, if you want to run the application using Docker, execute the commands below.
```bash
docker build -t dsr_event_creator .   
docker run -p 5001:5001 dsr_event_creator 
```
The app will then be available at `http://localhost:5001`.


<br>

## Project structure

```
├── .github/                    
│   └── workflows/          # GitHub Actions used when pushing code to the main branch in Github.
│
├── src/                    # Source code
│   ├── templates/          # HTML files (content of frontend)
│   ├── static/                
│   │   ├── style.css       # CSS files (style of frontend)
│   │   └── app.js/         # Javascript functions (functionality of frontend)
│   ├── app.py              # Flask server for the webpage (backend). Run this file to launch the web application.
│   ├── autofill_event.py   # Functionality to autofill a single event on Membersite using Selenium. 
│   ├── backend.py          # Functions to handle and validate data.
│   └── utils.py            # Simple helper functions. 
│
├── tests/                  # Files for testing the code (intended for Pytest)
│
├── .dockerignore           # List of files not included in the docker.
├── .gitignore              # List of files not syncronized with Git
├── Dockerfile              # Docker configuration file
├── README.md               # Project documentation
└── requirements.txt        # Python dependencies
```