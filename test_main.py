import pytest
from fastapi.testclient import TestClient
from main import app, Task, CreateTask, PredictRequest, PredictResponse, load_model

load_model()
client = TestClient(app)
task_id = None


@pytest.mark.dependency()
def test_create():
	response = client.post('/tasks', json={
		'task_name': 'example name',
		'task_description': 'for examle have to do some think'
		})

	assert response.status_code == 200
	assert response.json()['task_name'] == 'example name'
	assert response.json()['task_description'] == 'for examle have to do some think'
	assert response.json()['id'] == 1
	global task_id
	task_id = response.json()['id']


@pytest.mark.dependency(depends=['test_create'])
def test_get():
	response = client.get('/tasks')
	assert response.status_code == 200
	assert response.json()[0]['task_name'] == 'example name'
	assert response.json()[0]['task_description'] == 'for examle have to do some think'
	assert response.json()[0]['id'] == 1



@pytest.mark.dependency(depends=['test_create'])
@pytest.mark.parametrize('data, expected', [
	({'task_name': 'example name', 'task_description': 'for examle have to do some think'}, 400),
	({'task_name': 'changed name', 'task_description': 'changed task description' }, 200)
])
def test_update(data, expected):
	response = client.put(f'/tasks/{task_id}', json = data)
	assert response.status_code == expected
	if expected == 400:
		assert response.json()['detail'] == 'For data to change, there must be changes.'
	if expected == 200:
		assert response.json()['task_name'] == 'changed name'
		assert response.json()['task_description'] == 'changed task description'
		assert response.json()['id'] == 1


@pytest.mark.dependency(depends=['test_create'])
@pytest.mark.parametrize('id_param, expected', [
	(1, 200),
	(2, 404)
])
def test_delete(id_param, expected):
	response = client.delete(f'/tasks/{id_param}')
	assert response.status_code == expected
	if expected == 404:
		assert response.json()['detail'] == 'Task not found'
	if expected == 200:
		assert response.json()['message'] == f"Task where id = {id_param} has been deleted"


def test_data_to_csv():
	response = client.post('/sync-users')
	assert response.status_code == 200
	assert response.json()['message'] == 'The task of synchronizing user data is running in the background.'



def test_predict_priority():
	response = client.post('/predict', json={'task_description': 'Fix the problem with connecting to the database'})
	assert response.status_code == 200
	assert response.json()['task_description'] == 'Fix the problem with connecting to the database'
	assert response.json()['predicted_priority'] == 'high'






