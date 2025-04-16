# **Troubleshooting**


## **Common Issues & Solutions**

**1. FastAPI is not starting**

Possible Causes:

   - Uvicorn is not installed.
   - The FastAPI app is not correctly defined in main.py.
   - The required dependencies are missing.

Solution:

- Ensure Uvicorn is installed:

```bash
pip install uvicorn fastapi
```
- Run FastAPI using:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Check if main.py contains:

  ```
    python

    from fastapi import FastAPI

    app = FastAPI()
  ```

**2. Docker Container Fails to Start**
   
Possible Causes:

- The database container is not running.
- The ports in docker-compose.yml are conflicting.

Solution:

- Ensure MySQL is running:

```bash
docker ps
```

- If it's not running, start it with:

```bash
docker-compose up -d
```
- Check for port conflicts and update docker-compose.yml accordingly.


**3.  MySQL Connection Issues**

Possible Causes:

- Incorrect database credentials in .env or config.py.
- MySQL container is not running.

Solution:

- Verify credentials in .env or config.py:

```bash
MYSQL_USER=root
MYSQL_PASSWORD=root_password
MYSQL_DB=ipni
```
- Restart MySQL container:

```bash
docker-compose restart mysql
``` 

- Check logs for errors:

```bash
docker logs <container_id>

```

