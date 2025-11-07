Friends List Service: Backend & Telegram Bot

Test task for Junior Python Engineer

A FastAPI service with a Telegram bot for storing friends’ profiles with photos, professions, and AI-generated insights about their work.
This project implements a complete “Friends List” system, including a FastAPI backend integrated with AWS DynamoDB and AWS S3, as well as a Telegram bot for user interaction and optional LLM integration for profession analysis.

FastAPI service: http://13.53.137.205:8000/docs

Telegram Bot: @BuddyBaseBot

Technology Stack
Category	Technologies	Purpose
Backend	FastAPI, uvicorn, pydantic	API for managing friend data.
Storage	AWS DynamoDB, AWS S3, boto3	Data persistence and file storage.
Bot	python-telegram-bot	User interaction through Telegram.
LLM	openai (Async)	AI-based insights about professions.
Containers	Docker, Docker Compose	Containerization and orchestration.
Testing	pytest, httpx	Unit and integration testing for the API.
1. Setup / Installation
1.1. Prerequisites

Python 3.12+

Docker and Docker Compose

AWS Account and Credentials:
Ensure your local AWS profile is configured, or insert the keys directly into .env for boto3.

Service Configuration

AWS Setup (DynamoDB & S3)
Create a DynamoDB table and an S3 bucket via the AWS Console.
Also, create an IAM user or role with full CRUD access to these resources.
Add the generated Access Key ID and Secret Access Key to your AWS profile or .env file.

LLM Setup (OpenAI API)
To use the AI functionality, obtain an OpenAI API key from
https://platform.openai.com/docs/overview

and place it in the variable OPENAI_API_KEY inside your .env file.

1.2. Configuration & Environment Variables

Create a .env file in the project root using the template below.

.env.example

# === AWS Configuration ===
AWS_REGION=eu-north-1
TABLE_NAME=FriendsListTable # Name of your DynamoDB table
S3_BUCKET_NAME=friends-list-photos # Your unique S3 bucket name
S3_FOLDER=media/

# === Telegram Configuration ===
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
# Backend URL visible to the bot (used inside Docker Compose)
FASTAPI_URL=http://fastapi_backend:8000

# === LLM Configuration (Optional) ===
OPENAI_API_KEY=YOUR_OPENAI_API_KEY

2. Running the Project (Docker)
docker compose up --build


Verification:

Backend: http://localhost:8000

FastAPI Docs (OpenAPI): http://localhost:8000/docs

Stopping services:

docker compose down

3. API Endpoints and Examples

POST /friends
Create a new friend with profile data and photo (multipart/form-data).
Example:

curl -F "name=Alice" -F "profession=Engineer" -F "photo=@./alice.jpg" http://localhost:8000/friends


GET /friends
Retrieve all friends.

curl http://localhost:8000/friends


GET /friends/{id}
Retrieve a single friend by ID.

curl http://localhost:8000/friends/uuid-id-here


DELETE /friends/{id}
Delete a friend (removes from DynamoDB and deletes photo from S3).

curl -X DELETE http://localhost:8000/friends/uuid-id-here


POST /friends/{id}/ask
[LLM] Ask AI a question about the friend’s profession.

curl -X POST -H "Content-Type: application/json" -d '{"question":"What are the main challenges?"}' http://localhost:8000/friends/id/ask


GET /media/{s3_key:path}
Serve static images (proxy from S3).

curl -I http://localhost:8000/media/123-photo.jpg

4. Telegram Bot and Commands

The bot runs automatically in the telegram_bot_container.

Available Commands:

/start — Opens the main menu.

Add new friend — Step-by-step scenario (Photo → Name → Profession → Description).

Show all friends — Retrieves and displays all friends from the backend.

Find/Delete friend by ID — Requests an ID and performs the action.

Ask about profession (AI) — Requests an ID and a question for LLM.

5. Testing (Pytest)

API tests are automatically executed within the tests service when using Docker Compose.
They verify CRUD operations and data validation.

Run tests manually (inside the container or locally):

pytest

6. AWS Deployment & Architecture Notes

The project uses Option B (EC2 + Docker) for deployment.

Backend and Bot: Run as Docker containers on a single AWS EC2 instance using Docker Compose.

Data Persistence: Profile data stored in AWS DynamoDB, photos stored in AWS S3.

Architecture Diagram:

User → Telegram Bot → FastAPI → DynamoDB
                          ↓
                         S3 (photos)
                          ↓
                         OpenAI API (LLM)

7. Conclusion

The project implements a full interaction cycle between users and a FastAPI backend through Telegram,
utilizing AWS for data storage and LLM for extended AI-driven functionality.
The service is ready for further scaling, adding new bot commands,
and expanding analytical capabilities based on AI.
