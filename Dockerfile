# Use the official Python image.
# hadolint ignore=DL3006
FROM python:3.12.11-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code.
COPY . .

# Expose the port the app runs on.
EXPOSE 5000

# Command to run the application.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--keep-alive", "30", "run:app"]
