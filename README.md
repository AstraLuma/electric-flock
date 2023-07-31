# Electric Flock

Electric sheep, but live video stream

## Run server

First, get https://python-poetry.org/ , then set up the project:

    poetry install

to run the daemon:

    # With just:
    just serve
    # Without Just:
    poetry run flask --app electric_flock:app run --debug
