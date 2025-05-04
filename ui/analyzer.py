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
        "1) From the attached PDF, extract all key financial metrics and KPIs presented for the given period.\n"
        "2) Compute additional commonly used derived indicators if not explicitly stated, such as:\n"
        "   - Gross Margin = Gross Profit / Revenue\n"
        "   - Operating Margin = Operating Income / Revenue\n"
        "   - Net Margin = Net Income / Revenue\n"
        "   - Return on Assets (ROA) = Net Income / Total Assets\n"
        "   - EPS (if derivable), etc.\n"
        "3) Present all metrics in a single well-formatted ASCII table, wrapped in triple backticks:\n"
        "   - Use '|' as column separators\n"
        "   - Pad each cell so that all vertical lines align properly\n"
        "   - Include appropriate headers and column alignment\n"
        "   - If data is missing for a specific metric-period combination, explicitly fill the cell with 'NA'.\n"
        "   - Ensure the table is a complete rectangle with all rows and columns filled."
        "   - The first column(including Metric) should take up 30 characters in length, and the other columns should take up 15 characters in length\n"
        "4) After the table, write two sections:\n"
        "   a) 'Row Analysis:': One sentence per metric explaining its meaning and significance\n"
        "   b) 'Overall Summary:': A paragraph summarizing financial insights for this report\n"
        "5) Finally, under 'Visualization Suggestions:', recommend up to 3 types of charts that could effectively present this data to stakeholders.\n"
        "6) Do not include any unrelated commentary."
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
) -> tuple[str, str]:
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
        "1) Analyze the attached multiple PDF files, each of which represents a different financial period (e.g., different quarters or years).\n"
        "2) Extract comparable financial metrics across all periods, and compute derived metrics, such as:\n"
        "   - Gross Margin, Net Margin, ROA, Operating Margin\n"
        "   - Year-over-Year (YoY) or Quarter-over-Quarter (QoQ) growth\n"
        "   - EPS and other investor-relevant KPIs\n"
        "3) Build an ASCII table that summarizes the raw and computed metrics across all periods:\n"
        "   - Wrap it in triple backticks (```)\n"
        "   - Use '|' to separate columns and pad cells so vertical lines align\n"
        "   - Each row should represent a metric; each column a period (e.g., Q1 FY24, Q2 FY24, etc.)\n"
        "   - If data is missing for a specific metric-period combination, explicitly fill the cell with 'NA'.\n"
        "   - Ensure the table is a complete rectangle with all rows and columns filled."
        "   - The first column(including Metric) should take up 30 characters in length, and the other columns should take up 15 characters in length\n"
        "4) After the table, include the following sections:\n"
        "   a) 'Comparative Analysis:': Discuss significant trends, changes, and anomalies between periods\n"
        "   b) 'Risk Assessment:': Identify financial or operational risks implied by the data (e.g., declining margins, increasing debt, slowed revenue growth)\n"
        "   c) 'Strategic Insights:': Suggest potential areas for improvement or opportunities indicated by the data\n"
        "5) Under 'Visualization Suggestions:', recommend up to 3 charts (e.g., line, stacked bar) that would best highlight these comparative insights.\n"
        "6) Keep the output clean and professional, limited to the table and the four labeled sections."
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
        text = assistant_msg.content[0].text.value
    except Exception:
        text = assistant_msg.content
    return text, thread.id

def chat_with_openai(
    api_key: str,
    assistant_id: str,
    user_message: str,
    thread_id: str = None
) -> tuple[str, str]:
    """
    Send a plain-text chat message to the Assistants API and return the assistant's reply.
    """
    client = OpenAI(api_key=api_key)

    # Create thread and send message
    if thread_id:
        thread = client.beta.threads.retrieve(thread_id=thread_id)
    else:
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
        text = assistant_msg.content[0].text.value
    except Exception:
        text = assistant_msg.content
    return text, thread.id
