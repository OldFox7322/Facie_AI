import openai
import os
import asyncio
import logging
from database import get_one_friend
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()
logger = logging.getLogger(__name__)


class AIManager:
    def __init__(self, question: str, profession_data: Dict):
        self.question = question
        self.client = openai.AsyncOpenAI(api_key = os.getenv('OPENAI_APY_KEY'))
        self.profession = profession_data['Profession']
        self.profession_description = profession_data['ProfessionDescription']
        
    
    async def answers_to_questions(self):
        prompt = f'''
             Profession: {self.profession}, description: {self.profession_description}. Answer this question: {self.question}.
            If you understand at least 20 percent of the question, try to answer it. If you do not understand the question at all, indicate this and give an example of a correct question. Otherwise, just answer the question.
            Write your answer in the same language as the question, without emphasizing this.
            '''

        
        try:
            response = await self.client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {'role': 'system', 'content': 'You are an expert on professions and know everything about them. Answer the question.'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            logger.error(f"An unexpected error occurred for request:  {e}")
            return  None




