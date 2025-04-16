# Use a Python image that supports PDM
FROM python:3.12

# Set the working directory inside the container
WORKDIR /code


# Copy code
COPY . /code
RUN pip install .

# Start FastAPI
CMD ["fastapi", "run", "/code/src/ipni/main.py", "--port", "81"]


