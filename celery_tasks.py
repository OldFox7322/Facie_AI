import requests
import csv
import os 
import logging
from celery import Celery
from celery.schedules import crontab

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



celery_app = Celery('tasks', broker = 'redis://redis:6379/0')


celery_app.conf.beat_schedule = {
	'sync-users-every-30-minutes': {
	'task': 'celery_tasks.save_unique_data_to_csv',
	'schedule': crontab(minute="*/30"),
	'args': (),
	},
}








selection = ['id', 'name', 'email']



def get_data_from_api(url):
	try:
		response = requests.get(url)
		response.raise_for_status()
		return response.json()
	except requests.exception.RequestException as e:
		logging.error(f'Error receiving data from API: {e}')
		return


def get_existing_ids(csv_file):
	existing_ids = set()
	file_exist = os.path.isfile(csv_file)
	if file_exist:
		try:
			with open(csv_file, 'r', newline='', encoding='utf-8') as file:
				reader = csv.DictReader(file)
				for row in reader:
					existing_ids.add(int(row['id']))
		except (IOError, ValueError) as e:
			logging.error(f'Error reading file {csv_file}: {e}')
	return existing_ids


@celery_app.task
def save_unique_data_to_csv():
	url = 'https://jsonplaceholder.typicode.com/users'
	csv_file = 'users.csv'

	data = get_data_from_api(url)
	if not data:
		logging.warning('There is no new data to save.')
		return

	existing_ids = get_existing_ids(csv_file)

	unique_data = []
	for item in data:
		if int(item['id']) not in existing_ids:
			new_item = {field: item.get(field) for field in selection}
			unique_data.append(new_item)

	if not unique_data:
		logging.warning('No new unique data to save.')
		return

	headers = selection
	file_exist = os.path.isfile(csv_file)

	try:
		with open(csv_file, 'a', newline='', encoding='utf-8') as file:
			writer = csv.DictWriter(file, fieldnames=headers)
			if not file_exist:
				writer.writeheader()

			writer.writerows(unique_data)
		logging.info(f'Successfully added {len(unique_data)} new unique records to {csv_file}')
	except IOError as e:
		logging.error(f'Error writing to file: {e}')




