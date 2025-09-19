import pandas as pd
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
import joblib


logger = logging.getLogger(__name__)

def train_model():
	try:
		logging.info('Starting to read data from tasks.csv')
		df = pd.read_csv('tasks.csv')
		logging.info(f'Data successfully read. Found {len(df)} records.')

		X = df['task_description']
		y = df['priority']

		model = Pipeline([
			('vectorizer', TfidfVectorizer()),
			('classifier', MultinomialNB())
			])



		model.fit(X, y)
		logging.info('Model training completed.')

		joblib.dump(model, 'model.joblib')
		logging.info('Model successfully saved to model.joblib')
		return True 
	except FileNotFoundError:
		logging.error('The file tasks.csv was not found')
		return False
	except Exception as e:
		logging.error(f'An error occurred during model training: {e}')
		return False


if __name__ == '__main__':
	train_model()













