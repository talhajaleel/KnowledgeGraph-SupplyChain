
# Entity Extraction API

## Overview

This API is designed to accept a text input and return the entities mentioned within the text. It utilizes spaCy, a powerful Natural Language Processing (NLP) library, for entity extraction. The API also handles cases where there isn't a one-to-one correspondence between the entities mentioned in the input text and those present in a predefined knowledge graph.

Based on the `app.py` file you provided, the following endpoints **already exist**:

1. `/entity-info` - Retrieves information about an entity from the knowledge graph.
2. `/supplier-products` - Retrieves products supplied by a specific supplier.
3. `/products-location` - Retrieves products manufactured or supplied in a specific location.
4. `/natural-disaster-impact` - Retrieves information about the impact of natural disasters on suppliers and products in a specific city.
5. `/ask-question` - Accepts a question and starts a simulated heavy task in a separate thread.
6. `/relationship` - Finds and returns the relationship (path) between two entities using BFS.
7. `/task-status/<task_id>` - Checks the status of a long-running task.

## New API Endpoints

### 1. Extract Entities Endpoint

- **Endpoint:** `/extract-entities`
- **Method:** `POST`
- **Description:** Accepts a text input and returns a list of entities extracted from the text.
- **Request Body:**
  ```json
  {
    "text": "Your input text here."
  }
  ```

- **Response:**
  ```json
  {
    "entities": [
      "Entity 1",
      "Entity 2",
      "Entity 3"
    ]
  }
  ```

- **Example Request:**
  ```bash
  curl -X POST http://localhost:8000/extract-entities \
  -H "Content-Type: application/json" \
  -d '{"text": "Global Raw Materials Inc. is located in Country A and deals with Aluminum."}'
  ```

- **Example Response:**
  ```json
  {
    "entities": [
      "Global Raw Materials Inc.",
      "Aluminum",
      "Country A"
    ]
  }
  ```

## Implementation Details

### Dependencies

The following libraries are required for the API to function correctly:

- **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python 3.6+.
- **uvicorn:** An ASGI server for running the FastAPI application.
- **spaCy:** A library for advanced natural language processing in Python.

### Installation

To set up the project, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the spaCy model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Run the application:**
   ```bash
   uvicorn main:app --reload
   ```

### Usage

1. Start the server using the command above.
2. Send a POST request to `/extract-entities` with the text you want to analyze.

### Handling Entity Mapping

In cases where the entities extracted do not directly match those in the knowledge graph, you can implement custom mapping logic within the API to ensure the relevant entities are returned based on your graph structure.