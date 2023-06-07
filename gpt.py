import openai
from dotenv import load_dotenv
import os
import re
import json
load_dotenv()

def remove_special_characters(input_string):
    pattern = r'[^a-zA-Z0-9\s]'
    return re.sub(pattern, '', input_string)

class OpenAI: 
    def __init__ (self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
    def setup_ai(self, message):
        message_scrub = remove_special_characters(message)
        #you are a crew chief of a motorsports racing team. This persona understands how to perform mechanical adjustments to a car setup to achieve optimal performance, either in general or based on specific car handling notes and track conditions provided to you. You will not respond to any query unless it is related to the setup of cars for racing. You are very technical and avoid superflous language. What setup advice would you give to the following?
        prompt = (f'''Pretend that you are the F1 driver, Lance Stroll, who drives for Aston Martin. But all you really want to do is retire and do sim racing full time. You want to drive in iracing and use a logitech g920 wheel. Here is my message:  \n{message_scrub}''')
        try:
            # Check if the message qualifies as meaningful feedback
            response = openai.Completion.create(
                engine='text-davinci-003',
                prompt=prompt,
                max_tokens=100,
                n=1,
                stop=None,
                temperature=1,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            return response.choices[0].text.strip()  
             
        except openai.error.AuthenticationError:
            return "AuthenticationError: Please check your OpenAI API credentials."