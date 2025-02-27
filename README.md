# Active Meeting Listener


## Overview

Active Meeting Listener is a project designed to process and analyze meeting transcripts, with the main goal of generating meeting summaries from Microsoft Teams recordings. The project consists of several key components that work together:

- **Jupyter Notebook (meeting_assistant_agent.ipynb):**  
    This notebook implements the workflow for processing meeting content. It constructs a graph-based architecture using `langgraph` where different nodes handle tasks like speaker detection, text accumulation, keyword extraction, research, and summarization. The notebook supports both local models (using Ollama) and hosted models (such as OpenAI), making it flexible for different platforms.

- **VTT Parser (vttparser.py):**  
    This script converts Microsoft Teams VTT transcript files into structured JSON. It extracts metadata—such as speaker information, event IDs, timestamps—and consolidates the text for further processing. The parser also sorts and collates transcript records to enable effective testing and summarization by the notebook.

- **Dependency Installer (pip_reqs.sh):**  
    This shell script manages the installation of all necessary Python libraries. It ensures that all required dependencies (like langchain, langgraph, and related packages) are installed so that both the notebook and VTT parser can run seamlessly.

## Getting Started

1. **Install Dependencies:**  
     Run `pip_reqs.sh` to install the required packages:
     - Open your terminal.
     - Navigate to the project directory.
     - Execute:  
         `bash pip_reqs.sh`

2. **Prepare Transcript Files:**  
     Use the VTT parser to convert Microsoft Teams VTT transcript files into JSON. This JSON format is used for testing the summarization process in the notebook.

3. **Run the Notebook:**  
     Open `meeting_assistant_agent.ipynb` in Jupyter Notebook:
     - The notebook will prompt you for API keys required by various LLM integrations.
     - It processes meeting transcripts using a series of processing nodes defined in the graph workflow.
     - The output includes a comprehensive meeting summary with key points, action items, and technical terminology definitions.

## How It Works

- **Workflow:**  
    The project follows a clear sequence:
    1. The VTT parser converts the raw transcript into structured JSON.
    2. The JSON data is fed into the notebook where it navigates through various processing stages.
    3. The graph-based architecture ensures that each task (from speaker identification to final summarization) is handled modularly.
    4. Final outputs are logged and displayed, offering a complete meeting summary.

- **Modularity & Flexibility:**  
    The system is built in a modular fashion. The clear separation between the transcript parser, dependency installation, and processing notebook allows for easy updates and potential integration with other platforms or models.

This structured approach allows the project to be both robust and adaptable, making it a valuable tool for anyone looking to automate the process of generating meeting summaries from transcript data.