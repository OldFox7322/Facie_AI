from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status, Response
from models import FriendCreate, FriendResponse, Questions
from database import create_new_friend, upload_file_to_s3, get_file_from_s3, get_one_friend, get_all_friends, delete_friend, delete_file_from_s3
from fastapi.responses import StreamingResponse
from io import BytesIO
from answer_model import AIManager
import logging
MAX_FILE_SIZE = 8 * 1024 * 1024
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png"]
app = FastAPI(title = 'Friends DynamoDB & S3 API')


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.post('/friends', response_model = FriendResponse)
async def create_friend(
	name: str = Form(...),
	profession: str = Form(...),
	profession_description: str = Form(...),
	photo: UploadFile = File(...)
	):
	try:
		metadata = FriendCreate(name = name, profession = profession, profession_description = profession_description)
		friend_data_dict = metadata.model_dump(by_alias = True)
		filename = photo.filename if  photo.filename else ''

		result = create_new_friend(data = friend_data_dict, filename = filename)
		if not result:
			raise HTTPException(status_code = 500, detail = 'DynamoDB error when creating record')
		#
		file_content = await photo.read()
		if len(file_content) > MAX_FILE_SIZE:
			raise HTTPException(status_code = 400, detail = "File size limit (8MB) exceeded")
		s3_key = result['S3Key']
		upload_result_url = upload_file_to_s3(
			file_content = file_content,
			s3_key = s3_key,
			content_type = photo.content_type
			)
		if not upload_result_url:
			raise HTTPException(status_code = 500, detail = 'S3 upload failed')		
		return result

	except Exception as e:
		raise HTTPException(status_code = 500, detail = f'DB error: {e}')






@app.get('/friends', response_model = List[FriendResponse])
def get_friends():
	try:
		result = get_all_friends()
		if not result:
			raise HTTPException(status_code = 404,detail = 'No friends added found' )
		return result
	except Exception as e:
		raise HTTPException(status_code = 500, detail = f'DB error: {e}')




@app.get('/friends/{friend_id}', response_model = FriendResponse)  
def get_friend(friend_id: str):
	try:
		result = get_one_friend(friend_id)
		if not result:
			raise HTTPException(status_code = 404,detail = f'No found friend: {friend_id}')
		return result
	except Exception as e:
		raise HTTPException(status_code = 500, detail = f'DB error: {e}')



@app.get('/media/{s3_key:path}')
def get_photo_file(s3_key: str):
	try:
		file_content = get_file_from_s3(s3_key)
		if not file_content:
			raise HTTPException(status_code = 404, detail = f'No found file at S3 key: {s3_key}')
		content_type = "application/octet-stream"
		if s3_key.lower().endswith(('.jpg', '.jpeg')):
			content_type = "image/jpeg"
		if s3_key.lower().endswith('.png'):
			content_type = 'image/png'
		return StreamingResponse(BytesIO(file_content), media_type=content_type)
	except Exception as e:
		raise HTTPException(status_code = 500, detail = f'DB error: {e}')


@app.post('/friends/{friend_id}/ask', response_model = str)
async def answer_to_question(friend_id: str, question: Questions):
	try:
		result = get_one_friend(friend_id)
		if not result:
			raise HTTPException(status_code = 404,detail = f'No found friend: {friend_id}')
		ai_menager = AIManager(question.question, result)
		answer = await ai_menager.answers_to_questions()
		return answer
	except Exception as e:
		raise HTTPException(status_code = 500, detail = f'DB error: {e}')


@app.delete('/friends/delete/{friend_id}', response_model = str)
def delete_one_friend(friend_id: str):
	try:
		result = get_one_friend(friend_id)
		if result:
			x = delete_friend(friend_id)
			s3_key = result.get('S3Key')
			y = delete_file_from_s3(s3_key)
			return f'Friend: {friend_id} has been deleted'
	except Exception as e:
		raise HTTPException(status_code = 500, detail = f'DB error: {e}')
