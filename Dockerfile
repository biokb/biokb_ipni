FROM python:3.13-alpine
WORKDIR /code
COPY src ./src/
COPY pyproject.toml README.md ./
RUN pip install .
RUN mkdir -p /root/.biokb/ipni
CMD ["fastapi", "run","src/biokb_ipni/api/main.py"]