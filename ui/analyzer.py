import os
import time
from openai import OpenAI

def analyze_pdf_with_openai(
    pdf_path: str,
    api_key: str,
    assistant_id: str
) -> str:
    """
    Uploads a PDF using the Assistants API, runs the Assistant,
    """
    client = OpenAI(api_key=api_key)

    # 1. Upload the PDF (purpose="assistants")
    with open(pdf_path, "rb") as f:
        upload_resp = client.files.create(file=f, purpose="assistants")
    file_id = upload_resp.id

    # 2. Create a new conversation thread
    thread = client.beta.threads.create()

    # 3. Send a user message with the PDF attached
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="You are a financial analyst. Given the attached PDF, output a plain-text table of the key metrics per period.",
        attachments=[
            {
                "file_id": file_id,
                "tools": [{"type": "file_search"}]
            }
        ]
    )

    # 4. Create a run to invoke the Assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # 5. Poll until the run is complete
    while True:
        status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        ).status
        if status == "completed":
            break
        if status == "failed":
            raise RuntimeError("Assistant run failed")
        time.sleep(1)

    # 6. Retrieve all messages and return the assistant's reply
    msgs = client.beta.threads.messages.list(thread_id=thread.id).data
    assistant_msg = next(m for m in msgs if m.role == "assistant")
    try:
        return assistant_msg.content[0].text.value
    except Exception:
        return assistant_msg.content


def chat_with_openai(
    api_key: str,
    assistant_id: str,
    user_message: str
) -> str:
    """
    General chat interface using the same Assistant (no file attachments).
    """
    client = OpenAI(api_key=api_key)

    # 1. Create a new thread and send the user message
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    # 2. Create a run to invoke the Assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # 3. Poll until the run is complete
    while True:
        status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        ).status
        if status == "completed":
            break
        if status == "failed":
            raise RuntimeError("Assistant run failed")
        time.sleep(1)

    # 4. Retrieve and return the assistant's reply
    msgs = client.beta.threads.messages.list(thread_id=thread.id).data
    assistant_msg = next(m for m in msgs if m.role == "assistant")
    try:
        return assistant_msg.content[0].text.value
    except Exception:
        return assistant_msg.content
