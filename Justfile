# Show this help
help:
  @just --list

# Run a development server
serve:
  poetry run flask run --debug

# Run other flask commands
flask +ARGS:
  poetry run flask {{ARGS}}
