FROM python:3.12-alpine AS build
COPY my-compose-requirements.txt ./
RUN pip install --no-cache-dir -r my-compose-requirements.txt


FROM python:3.12-alpine
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY my-podman-compose.py ./
COPY compose.*.yml ./
CMD ["python", "./my-podman-compose.py", "-b", "pp", "up"]