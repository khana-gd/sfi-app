import os
import uuid
import logging
from datetime import datetime
from typing import Generator

# Setup logger for Google Workspace logs
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "google_integrations.log")

logging.basicConfig(level=logging.INFO)
workspace_logger = logging.getLogger("google_workspace")
handler = logging.FileHandler(LOG_FILE)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
workspace_logger.addHandler(handler)

# Mock Google Drive files store
MOCK_DRIVE_FILES = {
    "drive-file-1": {
        "name": "SFI Mughal Costume & Architecture Guidelines.pdf",
        "mime_type": "application/pdf",
        "content": b"%PDF-1.4 mock pdf contents for Mughal Costumes Study Guide"
    },
    "drive-file-2": {
        "name": "SFI Surface Draping & Cowl Neck Patterns.pdf",
        "mime_type": "application/pdf",
        "content": b"%PDF-1.4 mock pdf contents for Draping and Cowl Construction"
    }
}

class GoogleWorkspaceMockService:

    @staticmethod
    def stream_drive_file(file_id: str) -> Generator[bytes, None, None]:
        """Simulates streaming a Google Drive attachment from the backend API."""
        file_info = MOCK_DRIVE_FILES.get(file_id)
        if not file_info:
            workspace_logger.error(f"Google Drive attachment {file_id} not found.")
            raise FileNotFoundError("Google Drive file not found.")
        
        workspace_logger.info(f"Streaming Drive Attachment {file_id}: {file_info['name']}")
        chunk_size = 1024
        content = file_info["content"]
        for i in range(0, len(content), chunk_size):
            yield content[i:i + chunk_size]

    @staticmethod
    def create_calendar_event(title: str, start_time: datetime, description: str, user_email: str) -> str:
        """Simulates creating an academic milestone event in Google Calendar."""
        event_id = str(uuid.uuid4())
        log_message = (
            f"Google Calendar Event created for user: {user_email} | "
            f"Event ID: {event_id} | Title: '{title}' | "
            f"Start: {start_time.isoformat()} | Description: '{description[:50]}...'"
        )
        workspace_logger.info(log_message)
        print(log_message)  # Print to server stdout
        return event_id

    @staticmethod
    def export_to_google_doc(title: str, content_markdown: str, user_email: str) -> str:
        """Converts markdown contents to a mock HTML Google Doc openable in the browser."""
        doc_id = str(uuid.uuid4())
        
        # Pre-process content replacement to avoid backslashes in f-string expression
        html_body = content_markdown.replace('\n', '<br>')
        
        # Formulate a beautiful, formatted document
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title} - Google Docs Mock</title>
    <style>
        body {{
            background-color: #f8f9fa;
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 40px;
            color: #333;
        }}
        .docs-page {{
            background-color: #ffffff;
            width: 8.5in;
            min-height: 11in;
            margin: 0 auto;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            padding: 1in;
            box-sizing: border-box;
        }}
        .docs-header {{
            border-bottom: 2px solid #C9A65B;
            padding-bottom: 12px;
            margin-bottom: 30px;
            display: flex;
            justify_content: space-between;
            font-size: 12px;
            color: #777;
        }}
        h1 {{
            color: #0B132B;
            font-size: 28px;
            margin-top: 0;
        }}
        pre {{
            background: #f1f3f5;
            padding: 16px;
            border-radius: 6px;
            white-space: pre-wrap;
            font-size: 14px;
        }}
        p {{
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="docs-page">
        <div class="docs-header">
            <span>SFI KANHA Google Workspace Export</span>
            <span>Owner: {user_email}</span>
        </div>
        <h1>{title}</h1>
        <p><em>Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
        <div>
            {html_body}
        </div>
    </div>
</body>
</html>
"""
        # Save to static files directory so it can be served
        static_docs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "static", "google_docs"
        )
        os.makedirs(static_docs_dir, exist_ok=True)
        file_path = os.path.join(static_docs_dir, f"{doc_id}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        log_message = f"Google Doc created for user {user_email} | Doc ID: {doc_id} | Path: {file_path}"
        workspace_logger.info(log_message)
        print(log_message)
        
        # Return local static URL
        return f"http://localhost:8000/static/google_docs/{doc_id}.html"
