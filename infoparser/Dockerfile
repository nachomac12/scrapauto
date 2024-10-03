FROM python:3.11-slim

# Set environment variable
ENV PYTHONBUFFERED=1

# Set the working directory
WORKDIR /code

# Copy Pipfile and Pipfile.lock to the container
COPY pyproject.toml uv.lock /code/

# Install pipenv and project dependencies
RUN pip install uv && uv sync

# Copy the rest of the application code
COPY ./infoparser /code/

# Expose the backend port
EXPOSE 8100

# Run the application
CMD ["pipenv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8100", "--reload"]
