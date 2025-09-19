from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from celery_tasks import save_unique_data_to_csv
import uuid
import os
import joblib
import logging




class PredictResponse(BaseModel):
	task_description: str
	predicted_priority: str


class PredictRequest(BaseModel):
	task_description: str

class CreateTask(BaseModel):
	task_name: str
	task_description: str


class Task(BaseModel):
	id: int
	task_name: str
	task_description: str



logger = logging.getLogger(__name__)
app = FastAPI()
tasks: Dict[int, Task] = {}
task_id_counter = 0
ml_model = None



@app.get('/tasks', response_model = List[Task])
def get_tasks():
	return list(tasks.values())



@app.post('/tasks', response_model=Task)
def create_task(new_task: CreateTask):
	global task_id_counter 
	task_id_counter += 1

	result = Task(id = task_id_counter, **new_task.model_dump())
	tasks[task_id_counter] = result
	return result


@app.put('/tasks/{task_id}', response_model = Task)
def update_task(task_id: int, update_data: CreateTask):
	if task_id not in tasks:
		raise HTTPException(status_code=404, detail='Task not found')
	task = tasks[task_id]
	if (task.task_name == update_data.task_name and task.task_description == update_data.task_description):
		raise HTTPException(status_code=400, detail='For data to change, there must be changes.')
	result = Task(id = task_id, **update_data.model_dump())
	tasks[task_id] = result
	return result



@app.delete('/tasks/{task_id}')
def delete_task(task_id: int):
	if task_id not in tasks:
		raise HTTPException(status_code=404, detail='Task not found')
	del tasks[task_id]
	return {'message': f"Task where id = {task_id} has been deleted"}



@app.post('/sync-users')
def sync_users_data():
	save_unique_data_to_csv.delay()
	return {'message': 'The task of synchronizing user data is running in the background.'}

@app.on_event('startup')
def load_model():
	global ml_model
	model_path = 'model.joblib'
	if os.path.exists(model_path):
		ml_model = joblib.load(model_path)
		logging.info('ML model loaded successfully')
	else:
		raise RuntimeError('ML model file not found!')


@app.post('/predict', response_model = PredictResponse)
def predict_priority(request: PredictRequest):
	if ml_model is None:
		raise HTTPException(status_code=503, detail='ML model is not loaded yet')

	prediction = ml_model.predict([request.task_description])
	predicted_priority = prediction[0]

	return{'task_description': request.task_description, 'predicted_priority': predicted_priority}


