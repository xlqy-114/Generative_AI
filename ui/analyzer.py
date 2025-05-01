import os
import time
from openai import OpenAI

def analyze_pdf_with_openai(
    pdf_path: str,
    api_key: str,
    assistant_id: str
) -> str:
    """
    Upload and analyze a single PDF.
    """
    client = OpenAI(api_key=api_key)

    # 1) Upload the PDF
    with open(pdf_path, "rb") as f:
        upload_resp = client.files.create(file=f, purpose="assistants")
    file_id = upload_resp.id

    # 2) Create a conversation thread and send the prompt
    thread = client.beta.threads.create()
    prompt = (
        "You are a financial analyst.\n"
        "1) From the attached PDF, extract the key metrics per period.\n"
        "2) Construct an ASCII table, wrapped in triple backticks, using pipes (|) as column separators.\n"
        "   - Determine the maximum width of each column.\n"
        "   - Pad each cell with spaces so that every '|' in all rows lines up vertically.\n"
        "3) After the table code block, provide a narrative analysis:\n"
        "   a) Under 'Row Analysis:', write one sentence per metric explaining its significance.\n"
        "   b) Under 'Overall Summary:', write one brief paragraph summarizing the table's insights.\n"
        "4) Do not include any other text or commentary."
    )
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt,
        attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]}]
    )

    # 3) Trigger the assistant run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # 4) Poll until done
    while True:
        status = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        ).status
        if status == "completed":
            break
        if status == "failed":
            raise RuntimeError("Assistant run failed")
        time.sleep(1)

    # 5) Fetch and return the assistant's response
    messages = client.beta.threads.messages.list(thread_id=thread.id).data
    assistant_msg = next(m for m in messages if m.role == "assistant")
    try:
        return assistant_msg.content[0].text.value
    except Exception:
        return assistant_msg.content


def analyze_multiple_pdfs(
    pdf_paths: list[str],
    api_key: str,
    assistant_id: str
) -> str:
    """
    Upload multiple PDFs and perform one combined analysis.
    """
    client = OpenAI(api_key=api_key)

    # 1) Upload all PDFs
    attachments = []
    for path in pdf_paths:
        with open(path, "rb") as f:
            up = client.files.create(file=f, purpose="assistants")
        attachments.append({
            "file_id": up.id,
            "tools": [{"type": "file_search"}]
        })

    # 2) Create thread and send batch prompt
    thread = client.beta.threads.create()
    prompt = (
        "You are a financial analyst.\n"
        "1) Analyze all attached PDFs together and combine their key metrics into one table.\n"
        "2) Wrap the ASCII table in triple backticks:\n"
        "   - Use '|' separators and determine the maximum width per column.\n"
        "   - Pad each cell with spaces so that vertical lines align across all rows.\n"
        "3) After the code block, add narrative analysis:\n"
        "   a) 'Row Analysis:' with one sentence per metric.\n"
        "   b) 'Overall Summary:' one paragraph synthesizing insights.\n"
        "4) Only output the code block and the two analysis sections."
    )
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt,
        attachments=attachments
    )

    # 3) Trigger the assistant run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # 4) Poll until done
    while True:
        status = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        ).status
        if status == "completed":
            break
        if status == "failed":
            raise RuntimeError("Assistant run failed")
        time.sleep(1)

    # 5) Fetch and return the assistant's response
    messages = client.beta.threads.messages.list(thread_id=thread.id).data
    assistant_msg = next(m for m in messages if m.role == "assistant")
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
    Send a plain-text chat message to the Assistants API and return the assistant's reply.
    """
    client = OpenAI(api_key=api_key)

    # Create thread and send message
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    # Trigger run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # Poll until done
    while True:
        status = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        ).status
        if status == "completed":
            break
        if status == "failed":
            raise RuntimeError("Assistant run failed")
        time.sleep(1)

    # Fetch and return reply
    msgs = client.beta.threads.messages.list(thread_id=thread.id).data
    assistant_msg = next(m for m in msgs if m.role == "assistant")
    try:
        return assistant_msg.content[0].text.value
    except Exception:
        return assistant_msg.content
