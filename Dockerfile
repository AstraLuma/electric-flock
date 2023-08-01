FROM python:3-slim
WORKDIR /app
RUN pip install poetry
COPY . /app
RUN POETRY_VIRTUALENVS_CREATE=false poetry install --with=deploy

ENV PORT=80

VOLUME ["/app/segments"]
EXPOSE 80/tcp
CMD ["gunicorn", "electric_flock:app"]
