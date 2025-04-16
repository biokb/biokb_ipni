# **Installation Guide**

# **Getting Started**

## **Prerequisites**

- Python (3.8+)
- FastAPI
- Docker & Docker Compose
- MySQL Server & phpMyAdmin
- SQLAlchemy (for ORM)
- Uvicorn (for running FastAPI)

## **Installation Steps**

1. **Clone the repository**
    
    - git clone https://gitlab.informatik.uni-bonn.de/proglab-ii-24/projects/project_2.git
    - cd project_2

2. **Create a virtual environment**
    
    - python -m venv venv
    - source venv/bin/activate  # On Windows: venv\Scripts\activate
    - pip install -r requirements.txt
       
3. **Run the FastAPI application**

    - uvicorn main:app --reload

4. **Open your browser and navigate to http://127.0.0.1:8000**

5. **Run using Docker (Optional)**

    - docker-compose up --build
  
