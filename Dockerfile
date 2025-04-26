FROM python:3.11-slim

COPY requirements.txt /requirements.txt
COPY src /src
COPY styles /styles
COPY entrypoint.sh /entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
