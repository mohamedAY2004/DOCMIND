## Setup
#### Install Python with virtual environment handler with MiniConda
1) Download and install MiniConda from [here](https://docs.anaconda.com/free/miniconda/#quick-command-line-install) and add to system variables
2) Create a new environment using the following command:
```bash
$ conda create -n mini-rag python=3.10
```
3) Activate the environment:
```bash
$ conda activate mini-rag
```
## Installation

### Install the required packages
```bash
$ pip install -r requirements.txt
```
### Setup the environment variables and add your values
```bash
$ cp .env.example .env
```

## Run docker Compose Services

```bash
$ cd docker
$ sudo docker compose up -d
```
- update `.env` with your credintials 
#### Run the fast api server
```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 5000
```
 