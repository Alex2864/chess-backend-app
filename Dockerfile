# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including the Stockfish engine itself
# and the 'which' command to find its path
RUN apt-get update && apt-get install -y stockfish which

# THIS IS THE CRITICAL NEW LINE:
# Find the full path to the stockfish executable and save it in an environment variable
ENV STOCKFISH_PATH /usr/games/stockfish

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container at /app
COPY . .

# Make port 10000 available to the world outside this container
EXPOSE 10000

# Define the command to run your app using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "main:app"]
