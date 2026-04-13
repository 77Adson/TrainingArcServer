import os

# Set the environment variable before Pytest collects and imports the app modules
os.environ["JWT_SECRET_KEY"] = "test-secret-key"