import math
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile
import os
import openai
from reportlab.lib import colors
from reportlab.lib.colors import Color


class RoadmapTool():

    def _run(self, topic: str, num_steps: int) -> str:
        try:
            # Generate roadmap content using OpenAI
            roadmap_content = self._generate_roadmap_content(topic, num_steps)
            
            # Create an interactive PDF
            temp_dir = tempfile.mkdtemp()
            pdf_path = os.path.join(temp_dir, 'interactive_roadmap.pdf')
            self._create_interactive_pdf(roadmap_content, pdf_path)

            return f"Interactive roadmap generated and saved as {pdf_path}"
        except Exception as e:
            return f"Error: {e}"
        
    def _generate_each_page(self, subtitle)-> List[dict]:
        prompt = f"""Generate a python list in which 3 actions are there for each subtitle in {subtitle}. For each step, provide:
        1. A short title (max 5 words)
        2. short subtitles (max 5 words)
        Format the response as a Python list of dictionaries, where each dictionary has 'title', "subtitles' keys."""
        response = self._get_openai_response(prompt)
        print("response", response)
        
        try:
            # Parse the response into a list of dictionaries
            roadmap_content = eval(response)
            return roadmap_content
        except:
            # Fallback in case of parsing error
            return [{"title": f"Step {i+1}", "description": f"Description for step {i+1}", "actions": ["Action 1", "Action 2"]} for i in range(3)]


    def _generate_roadmap_content(self, topic: str, num_steps: int) -> List[dict]:
        prompt = f"""Generate a {num_steps}-step roadmap for {topic}. For each step, provide:
        1. A short title (max 5 words)
        2. short 3 subtitles (max 5 words)
        Format the response as a Python list of dictionaries, where each dictionary has 'title', "subtitles' keys."""
        response = self._get_openai_response(prompt)
        print("response", response, type(response))

        
        if isinstance(response, list):
            return response
        else:
            # Fallback in case of parsing error
            print(f"Error in generate roadmap: {response}")
            return [{"title": f"Step {i+1}", "subtitles": ["subtitle 1", "subtitle 2", "subtitle 3"]} for i in range(num_steps)]
    def _get_openai_response(self, prompt):
        try:
            openaiclient = openai.Client(
                api_key=os.getenv('OPENAI_API_KEY'),
                base_url=os.getenv('OPENAI_BASE_URL')
            )
            syss = """
            You are an AI assistant specializing in creating detailed roadmaps. 
            Your task is to generate comprehensive and practical steps for the given topic.
            Each step should have a clear title, a concise description, and key actions to take.
            Ensure the steps are logical, progressive, and relevant to the topic.
            """

            msg = [
                {"role": "system", "content": syss},
                {"role": "user", "content": prompt},
            ]
            response = openaiclient.chat.completions.create(
                messages=msg,
                temperature=0.6,
                model=os.getenv('OPENAI_MODEL'),
                max_tokens=350,
                stream=False,
            )
            content = response.choices[0].message.content
            parsed_response = self._parse_llm_response(content)
            if parsed_response is None:
                return f"Error: Unable to parse the LLM response"
            return parsed_response
        except Exception as e:
            return f"Error generating content: {e}"
        
    
    
    
    def _get_pastel_color(self, index, light=False):
        color_list = [
            (255, 179, 186), (255, 223, 186), (255, 255, 186), (186, 255, 201),
            (186, 225, 255), (186, 186, 255), (255, 186, 255), (223, 186, 255)
        ]
        r, g, b = color_list[index % len(color_list)]
        if light:
            r, g, b = [(c + 255) // 2 for c in (r, g, b)]
        return Color(r/255, g/255, b/255)


    def _parse_llm_response(self, response):
        try:
            # Find the start and end of the list in the response
            list_start = response.find('[')
            list_end = response.rfind(']') + 1
            
            if list_start == -1 or list_end == -1:
                raise ValueError("No list found in the response")
            
            # Extract the list string
            list_str = response[list_start:list_end]
            
            # Parse the list string into a Python object
            parsed_list = eval(list_str)
            
            if not isinstance(parsed_list, list):
                raise ValueError("Parsed content is not a list")
            
            return parsed_list
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return None
        

    def _create_interactive_pdf(self, roadmap_content: List[dict], output_path: str):
        print("roadmap", roadmap_content)
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        # First page: Mind Map
        c.bookmarkPage('roadmap')
        c.addOutlineEntry("Roadmap Overview", 'roadmap', 0)
        
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 50, "Roadmap Overview")

        # Draw mind map
        center_x, center_y = width / 2, height / 2
        main_topic_radius = 80
        subtopic_radius = 60
        
        # Main topic
        c.setFillColor(colors.lightblue)
        c.circle(center_x, center_y, main_topic_radius, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 14)
        self._draw_wrapped_text(c, "Roadmap", center_x - main_topic_radius + 10, center_y + 10, main_topic_radius * 2 - 20, 16)

        # Subtopics
        for i, step in enumerate(roadmap_content):
            angle = i * (2 * math.pi / len(roadmap_content))
            distance = main_topic_radius + subtopic_radius + 40
            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)
            
            # Draw branch
            c.setStrokeColor(colors.gray)
            c.line(center_x, center_y, x, y)
            
            # Draw subtopic circle
            c.setFillColor(self._get_pastel_color(i))
            c.circle(x, y, subtopic_radius, fill=1)
            
            # Draw step title
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 10)
            self._draw_wrapped_text(c, step['title'], x - subtopic_radius + 5, y + subtopic_radius - 15, subtopic_radius * 2 - 10, 12)
            
            # Add link to detailed page
            c.linkRect(f"step_{i}", f"step_{i}", (x - subtopic_radius, y - subtopic_radius, x + subtopic_radius, y + subtopic_radius), thickness=0)

            # Draw sub-subtopics
            for j, action in enumerate(step['subtitles'][:3]):  # Limit to 3 actions for simplicity
                sub_angle = angle + (j - 1) * (math.pi / 8)
                sub_distance = distance + subtopic_radius + 30
                sub_x = center_x + sub_distance * math.cos(sub_angle)
                sub_y = center_y + sub_distance * math.sin(sub_angle)
                
                # Draw branch to sub-subtopic
                c.setStrokeColor(colors.gray)
                c.line(x, y, sub_x, sub_y)
                
                # Draw sub-subtopic circle
                c.setFillColor(self._get_pastel_color(i, light=True))
                c.circle(sub_x, sub_y, 25, fill=1)
                
                # Draw action text
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 8)
                self._draw_wrapped_text(c, action, sub_x - 20, sub_y + 10, 40, 10)
        c.showPage()
    

            # Create a page for each step
        
        
        for i, step in enumerate(roadmap_content):
            c.bookmarkPage(f"step_{i}")
            c.addOutlineEntry(f"Step {i+1}: {step['title']}", f"step_{i}", 1)
            
            c.setFont("Helvetica-Bold", 16)
            title = f"Step {i+1}: {step['title']}"
            wrapped_title = self._wrap_text(title, 60)
            text_object = c.beginText(inch, height - inch)
            text_object.textLines(wrapped_title)
            c.drawText(text_object)
            
            y_offset = 2*inch
            subtitles=roadmap_content[i]["subtitles"]
            print("subtitles", subtitles)
            prompt=f"""Generate 3 actions for each 'subtitles' in the list {subtitles}. For each subtitle, provide:
            1. 3 actions (max 5 words)
            Format the response as a Python list of dictionaries, where each dictionary has 'subtitle', "actions' keys."""
            response_page = self._get_openai_response(prompt)
            
            print("response", response_page)
            
            if isinstance(response_page, str):
                response_page=eval(response_page)
                
            else:
                
                pass
            for response in response_page:
                # Draw subtitle
                c.setFont("Helvetica-Bold", 14)
                wrapped_subtitle = self._wrap_text(response['subtitle'], 70)
                text_object = c.beginText(inch, height - y_offset)
                text_object.textLines(wrapped_subtitle)
                c.drawText(text_object)
                
                y_offset += 0.5*inch
                
                # Add key actions
                c.setFont("Helvetica", 12)
                for action in response['actions']:
                    wrapped_action = self._wrap_text(action, 80)
                    text_object = c.beginText(inch + 20, height - y_offset)
                    text_object.textLines(f"• {wrapped_action}")
                    c.drawText(text_object)
                    y_offset += 0.5*inch * (wrapped_action.count('\n') + 1)
                
                y_offset += 0.5*inch  # Add some space between subtitle
            
            # Add a back button
            c.setFont("Helvetica", 10)
            c.rect(inch, inch, 80, 30, fill=0)
            c.drawCentredString(inch + 40, inch + 15, "Back to Overview")
            c.linkRect("back_to_overview", 'roadmap', (inch, inch, inch + 80, inch + 30), thickness=0)
            
            c.showPage()

        c.save()

    def _wrap_text(self, text, width):
        """Wrap text to a specified width."""
        lines = []
        for paragraph in text.split('\n'):
            line = []
            for word in paragraph.split():
                if len(' '.join(line + [word])) <= width:
                    line.append(word)
                else:
                    lines.append(' '.join(line))
                    line = [word]
            lines.append(' '.join(line))
        return '\n'.join(lines)

    def _draw_wrapped_text(self, canvas, text, x, y, width, line_height):
        """Draw wrapped text on the canvas."""
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            if canvas.stringWidth(' '.join(current_line + [word])) <= width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        
        for i, line in enumerate(lines):
            canvas.drawString(x, y - i*line_height, line)

    
