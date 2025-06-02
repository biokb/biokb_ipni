# IPNI

🌱 The `ipni` library is designed to ...
- load
- query and 
- analyse 

data from the [International Plant Names Index](https://www.ipni.org/) (IPNI) database

Main features of the library are:

1. Relational database 
2. FastAPI

## Background on IPNI

The International Plant Names Index (IPNI) is a database of plant names, including botanical names of seed plants, ferns, and lycophytes. It provides authoritative information on scientific names, authors, and publication details, helping researchers ensure accurate plant nomenclature. IPNI is a collaborative project between [The Royal Botanic Gardens, Kew](https://www.kew.org/), [The Harvard University Herbaria](https://www.huh.harvard.edu/), and [The Australian National Herbarium](https://www.anbg.gov.au/cpbr/herbarium/). It is freely accessible online and plays a crucial role in botanical taxonomy and plant classification.

Creating your own FastAPI application with IPNI data in your own database can provide several advantages, depending on your goals. Below are some key motivations:

## Motivation for this project

Creating a FastAPI application with IPNI data in a local relational database can provide several advantages:

- **Performance & Speed Optimization**
  - *Faster Queries*: Instead of relying on IPNI’s web interface or API (which may have rate limits or latency), a local database enables instant and fast lookups
  - *Optimized Indexing*: You can index your database based on name, author, or publication year to enhance search efficiency
  - *Batch Processing*: Perform bulk queries and cross-referencing faster than using IPNI’s online tools

- **Custom Features & Enhancements**
  - *Advanced Search Filters*: Add filters like date range, geographic region, plant family, synonymy status, etc.
  - *Fuzzy Searching*: Implement approximate name matching (e.g., handling typos or alternative spellings).
  - *Full-Text Search*: Use powerful search engines like MySQL’s full-text search to allow partial or phonetic matches.

- **Offline Access & Data Ownership**
  - *Work Without Internet*: Useful for remote field research or areas with limited connectivity.
  - *Ensure Data Availability*: If IPNI goes down or changes API policies, you still have your data.
  - *Control Updates & Backups*: Keep track of changes in scientific names, authors, and publications over time.

- **API Customization for Specific Needs**
  - *Create a Tailored API*: Unlike IPNI’s general API, your FastAPI service can match your organization’s requirements.
  - *Rate Limit Control*: No external API limits—your app can handle as many queries as needed.
  - *Provide Data as JSON, CSV, or XML* : Serve plant name data in different formats based on user requirements.

## Getting started 
1. **Clone the repository**

```bash 
git clone https://gitlab.informatik.uni-bonn.de/proglab-ii-24/projects/project_2.git
cd project_2 
python -m venv venv
source venv/bin/activate 
pip install .
```
OR use PDM
```python
pdm install
``` 

2. **Requirements** 
- python3.12 or higher 
- Git 
- Docker Desktop
- SQLite
- MySQL
- SQLAlchemy
- FastAPI 
- Pandas 

3. **Install Docker Desktop** 
Link : https://www.docker.com/products/docker-desktop/
4. Docker should be running on your machine, allowing you to build, run and manage containers.

```python
podman-compose up -d
``` 

5. **Run the FastAPI server**
- Run the data migration endpoints 
- The password is : root_passwd

```python
uvicorn main:app --reload
```

## Build and run Docker

```bash
podman build -t ipni-image . && podman run --replace -p 8000:8000 --name ipni-container -d ipni-image
```


## Features 

Project 2 is a Python library with the following features:

- **SQLAlchemy** for object-relational mapping (ORM) that defines databse models.
- **Primary and foreign key management**: Establish relationships between different tables using object-relational mapping.
- **MySQL**: A full-featured database server designed for handling large-scale applications.
- **SQLite**: A self-contained database.
- **FastAPI** framework:web framework for building APIs with Python
- **Docker**: Containerizes the package, manages, and deploys services.

