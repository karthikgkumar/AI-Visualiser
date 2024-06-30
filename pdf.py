
import requests
import io
import os

class PDFCreationTool():

    def _run(self, topic: str,num_pages: int) -> str:
        
        try:
            
            api_url=os.getenv('AWS_URL_PDF')
            payload = {
                "topic": topic,
                "num_pages": num_pages,
                }
            
            url = os.getenv('LOGIN_URL')  # Replace with the actual URL
            payload_api = {
                "email": os.getenv('EMAIL'),
                "password": os.getenv('PASSWORD'),
                "os": "browser",
                "deviceName": "moto g82"
            }

            # Send the POST request
            response_session = requests.post(url, json=payload_api)

            # Check if the request was successful
            if response_session.status_code == 200:
                data = response_session.json()
                session_id = data.get("token")
                if data.get("verifiedUser"):
                    session_id = data.get("token")
                    print("Session ID:", session_id)
                else:
                    print("Authentication failed:", data.get("message"))
            else:
                print("Request failed with status code:", response_session.status_code)
            
            # Get the streaming response
            with requests.post(api_url, json=payload, stream=True) as response:
                response.raise_for_status()
                
                # Read the streaming content into a BytesIO object
                content = io.BytesIO()
                print(content)
                for chunk in response.iter_content(chunk_size=8192):
                    content.write(chunk)
                
                # Reset the BytesIO object to the beginning
                content.seek(0)
                
                # Prepare the file for upload
                filename = f"{payload['topic'].replace(' ', '_')}_presentation.pdf"
                files = {
                    "file": (filename, content, "application/pdf")
                }
                print(files)
                server_auth_token=session_id
    
                # Upload the file
                headers_server = {"Authorization": f"Bearer {server_auth_token}"}
                upload_url = os.getenv("CLOUD_UPLOAD_URL")
                
                upload_response = requests.post(
                    upload_url,
                    headers=headers_server,
                    files=files,
                    stream=True
                )
                print(upload_response.text)
                upload_response.raise_for_status()
                download_link = upload_response.json()["location"]
                
                
                return f"PDF created and uploaded. Download link: {download_link}"

        except Exception as e:
            return f"Error creating presentation: {str(e)}. Please try again or contact support if the issue persists."

    def _arun(self, topic: str, format: str, num_slides: int):
        raise NotImplementedError("This tool cannot be used asynchronously.")
