import chainlit as cl
from pydantic import BaseModel, Field
from typing import Optional
import openai
from roadmap import RoadmapTool
from presentation import PresentationTool
from pdf import PDFCreationTool
import os

class AiVisualiserArgs(BaseModel):
    action: str = Field(
        description="The action to perform: 'create_presentation' or 'create_pdf' or 'create_roadmap'.",
        enum=["create_presentation", "create_pdf", "create_roadmap"],
    )
    topic: str = Field(description="The topic for which to generate a roadmap or pdf or presentation")
    num_steps: int = Field(description="Number of steps in the roadmap", default=3)
    num_slides: int = Field(description="Number of slides to create (1-10)", default=5)
    theme: str = Field(
        description="Theme of the presentation: 'light', 'dark', 'professional', 'creative', 'minimalist', or 'tech'",
        default='light'
    )
    num_pages: int = Field(description="Number of pages in the presentation", default=2)

class AIVisualizer:
    def run(self, action: str, topic: str, num_steps: Optional[int] = None, num_pages: Optional[int] = None, theme: Optional[str] = None, num_slides: Optional[int] = None):
        if action == "create_roadmap":
            roadmap = self.roadmap(topic, num_steps)
            return roadmap
        elif action == "create_presentation":
            return self.create_presentation(topic, num_slides, theme)
        elif action == "create_pdf":
            return self.pdf_create(topic, num_pages)
        else:
            return "Error: Invalid action specified."

    def roadmap(self, topic: str, num_steps: int) -> str:
        roadmap = RoadmapTool()
        return roadmap._run(num_steps=num_steps, topic=topic)

    def create_presentation(self, topic: str, num_slides: int, theme: str) -> str:
        presentation = PresentationTool()
        return presentation._run(topic=topic, num_slides=num_slides, theme=theme)

    def pdf_create(self, topic: str, num_pages: int) -> str:
        pdf = PDFCreationTool()
        return pdf._run(topic=topic, num_pages=num_pages)

sys_prompt = """
You are a helpful assistant that can create visual aids such as roadmaps, presentations, and PDFs on various topics. The user will provide the action (create_roadmap, create_presentation, or create_pdf) and the topic, along with optional parameters. You will use the 'ai_visualizer' tool to generate the requested visual aid.

When the user specifies an action and topic, use the 'ai_visualizer' tool with the appropriate arguments. The tool will generate the requested visual aid based on the given parameters.

Respond politely and provide the output from the tool.
"""

tools = [
    {
        "type": "function",
        "function": {
            'name': 'ai_visualizer',
            'description': 'Generates visual aids such as roadmaps, presentations, and PDFs on a given topic.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'action': {
                        'type': 'string',
                        'enum': ['create_roadmap', 'create_presentation', 'create_pdf'],
                        'description': 'The action to perform: create_roadmap, create_presentation, or create_pdf.'
                    },
                    'topic': {
                        'type': 'string',
                        'description': 'The topic for which to generate a roadmap, presentation, or PDF.'
                    },
                    'num_steps': {
                        'type': 'integer',
                        'description': 'Number of steps in the roadmap (default: 3).'
                    },
                    'num_slides': {
                        'type': 'integer',
                        'description': 'Number of slides to create (1-10, default: 5).'
                    },
                    'theme': {
                        'type': 'string',
                        'enum': ['light', 'dark', 'professional', 'creative', 'minimalist', 'tech'],
                        'description': 'Theme of the presentation (default: light).'
                    },
                    'num_pages': {
                        'type': 'integer',
                        'description': 'Number of pages in the PDF (default: 2).'
                    }
                },
                'required': ['action', 'topic']
            }
        }
    }
]

openaiclient = openai.Client(
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url=os.getenv('OPENAI_BASE_URL'),
)

def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    try:
        with open(readme_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "README.md not found."

@cl.on_chat_start
async def start():
    cl.user_session.set("messages", [{"role": "system", "content": sys_prompt}])
    
    readme_content = read_readme()
    await cl.Message(content=readme_content).send()

@cl.on_message
async def main(message: cl.Message):
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": message.content})

    response = openaiclient.chat.completions.create(
        model=os.getenv('OPENAI_MODEL'),
        messages=messages,
        tools=tools,
        max_tokens=1200,
        stream=False,
    )

    response_message = response.choices[0].message
    messages.append({"role": "assistant", "content": response_message.content})

    await cl.Message(content=response_message.content).send()

    tool_calls = response_message.tool_calls
    if tool_calls:
        tool_call = tool_calls[0]
        tool_call_id = tool_call.id
        tool_function_name = tool_call.function.name
        tool_args = eval(tool_call.function.arguments)

        if tool_function_name == 'ai_visualizer':
            ai_viz = AIVisualizer()
            results = ai_viz.run(**tool_args)
            messages.append({
                "role": "tool", 
                "tool_call_id": tool_call_id, 
                "name": tool_function_name, 
                "content": results
            })

            model_response_with_function_call = openaiclient.chat.completions.create(
                model=os.getenv('OPENAI_MODEL'),
                messages=messages,
            )
            final_response = model_response_with_function_call.choices[0].message.content
            messages.append({"role": "assistant", "content": final_response})
            await cl.Message(content=final_response).send()
        else:
            error_message = f"Error: function {tool_function_name} does not exist"
            await cl.Message(content=error_message).send()
    
    cl.user_session.set("messages", messages)