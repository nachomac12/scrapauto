FROM python:3.12-slim

# Set environment variable
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /code

# Copy Pipfile and Pipfile.lock to the container
COPY pyproject.toml uv.lock /code/

# Install uv and project dependencies
RUN pip install uv && uv sync

# Copy the rest of the application code
COPY . /code

# Expose the backend port
EXPOSE 8100

# Run the application
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8100", "--reload"]
