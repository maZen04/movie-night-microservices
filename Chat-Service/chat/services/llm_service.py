from groq import Groq
from django.conf import settings
import json



class LLMService:

    def __init__(self):
        self.client = Groq(
            api_key=settings.GROQ_API_KEY
        )
    
    def test_models(self):
        models = self.client.models.list()

        for model in models.data:
            print(model.id)

    def recommend_movie(self, answers):

        prompt = f"""
        You are a movie recommendation assistant.

        Based on the user's answers, recommend one movie (always return one movie not more not less).

        User answers:
        {json.dumps(answers, ensure_ascii=False)}

        Return ONLY valid JSON in this exact format:

        {{
            "movie_title": "Movie title"
        }}
        """

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful movie recommendation assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content

        return json.loads(content)