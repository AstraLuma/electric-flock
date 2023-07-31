# Show this help
help:
  @just --list

# Run a development server
serve:
  poetry run flask --app electric_flock:app run --debug
