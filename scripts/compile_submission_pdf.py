import os
import sys
import subprocess
import re
import zlib
import base64
import hashlib
import urllib.request
from datetime import datetime

def check_dependencies():
    try:
        import markdown
    except ImportError:
        print("Installing required 'markdown' library for PDF generation...")
        subprocess.run([sys.executable, "-m", "pip", "install", "markdown"], check=True)
        import markdown

check_dependencies()
import markdown

def get_kroki_diagram(diagram_text, screenshots_dir):
    """
    Compresses mermaid diagram and fetches SVG from Kroki,
    saving it locally and returning the local file:// URL.
    """
    diagram_text = diagram_text.strip()
    
    diagram_hash = hashlib.md5(diagram_text.encode('utf-8')).hexdigest()
    svg_filename = f"diagram_{diagram_hash}.svg"
    svg_path = os.path.join(screenshots_dir, svg_filename)
    
    if not os.path.exists(svg_path):
        try:
            compressed = zlib.compress(diagram_text.encode('utf-8'), 9)
            encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
            url = f"https://kroki.io/mermaid/svg/{encoded}"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                with open(svg_path, 'wb') as out_file:
                    out_file.write(response.read())
            print(f"  -> Rendered and saved diagram to docs/screenshots/{svg_filename}")
        except Exception as e:
            print(f"  [Warning] Failed to fetch diagram SVG from Kroki: {e}")
            return None
            
    file_url = "file:///" + svg_path.replace("\\", "/")
    return file_url

def run():
    print("=" * 60)
    print("      PulseQueue Assignment PDF Submission Compiler")
    print("=" * 60)
    print("This script will combine your documentation, diagrams, and screenshots")
    print("into a single submission-ready PDF file.")
    print("-" * 60)

    # Prompt details
    name = input("Enter your Name: ").strip() or "Chavan Rupesh Sharan"
    reg_num = input("Enter your Registration Number: ").strip() or "RA2311026010210"
    github_url = input("Enter your GitHub Repository URL (optional): ").strip() or "https://github.com/RupeshSharan/Codity.ai_assigment.git"

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(root_dir, "docs")
    screenshots_dir = os.path.join(docs_dir, "screenshots")

    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        print(f"\n[Notice] Created screenshot folder at: {screenshots_dir}")

    files_to_merge = [
        ("README.md", "README.md"),
        ("System Architecture", "docs/ARCHITECTURE.md"),
        ("Database Design & Relations", "docs/DATABASE_DESIGN.md"),
        ("ER Diagram Structure", "docs/ER_DIAGRAM.md"),
        ("API Documentation", "docs/API.md"),
        ("Design Decisions & Trade-offs", "docs/DESIGN_DECISIONS.md"),
        ("User Operations Manual", "docs/USER_MANUAL.md"),
        ("Automated Testing Report", "docs/TESTING.md"),
        ("Completed Milestones & Next Steps", "docs/NEXT_STEPS.md")
    ]

    html_content = []

    # 1. Add Cover Page
    current_date = datetime.now().strftime("%B %d, %Y")
    cover_page = f"""
    <div class="cover-page">
        <div class="logo">PQ</div>
        <h1>PulseQueue</h1>
        <h2>A Production-Inspired Distributed Job Scheduling Platform</h2>
        <div class="divider"></div>
        <div class="meta-container">
            <div class="meta-item"><strong>Student Name:</strong> {name}</div>
            <div class="meta-item"><strong>Registration Number:</strong> {reg_num}</div>
            <div class="meta-item"><strong>Submission Date:</strong> {current_date}</div>
            {f'<div class="meta-item"><strong>GitHub Repository:</strong> <a href="{github_url}">{github_url}</a></div>' if github_url else ''}
        </div>
        <div class="page-footer">Intern Assignment Submission - Production Engineering Track</div>
    </div>
    <div class="page-break"></div>
    """
    html_content.append(cover_page)

    # 2. Add Personal Statement (Humanising the submission)
    personal_statement = f"""
    <div class="section-container">
        <h1>Executive Summary & Personal Engineering Approach</h1>
        <p><strong>Submitted by:</strong> {name} ({reg_num})</p>
        <p>When approaching the challenge of building a distributed job scheduler, it is easy to focus solely on the happy path—submitting a task and watching a worker run it. However, in real production environments, systems fail. Networks partition, workers crash mid-execution, database loads spike, and concurrent clients trigger race conditions.</p>
        
        <p>For this assignment, my design philosophy for <strong>PulseQueue</strong> centered on <strong>correctness, fault-tolerance, and high observability</strong> over a checklist of secondary features. I wanted to design a developer-first platform that remains reliable under stress. Rather than treating background processing as an abstracted black box, I built it as a visible, auditable developer console where every single state change, failure retry, and worker heartbeat is preserved and easily inspected.</p>

        <h3>Key Architectural Pillar Decisions:</h3>
        <ul>
            <li><strong>Relational Integrity over Cache-Only Claims:</strong> Storing core lifecycle states in a relational database (PostgreSQL) ensures transactional consistency. If the worker runner crashes, the state is persisted and recoverable, rather than lost in volatile memory.</li>
            <li><strong>Atomic Claim Locking:</strong> Using atomic status updates (and `FOR UPDATE SKIP LOCKED` on PostgreSQL) guarantees that no two workers can ever claim the same job, preventing double-billing or duplicate notification dispatches.</li>
            <li><strong>Observability first:</strong> By designing structured logs that record execution attempt timelines (attempt durations, specific worker identifiers, and exit stack traces), operators can debug pipeline stalls in seconds directly from the React console.</li>
        </ul>
        <p>In the following sections, this report documents the database modeling details, REST API contracts, and concurrency reliability testing built to validate this system.</p>
    </div>
    <div class="page-break"></div>
    """
    html_content.append(personal_statement)

    # Regex to extract mermaid code blocks
    mermaid_pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)

    # 3. Append markdown docs
    for title, rel_path in files_to_merge:
        full_path = os.path.join(root_dir, rel_path)
        if not os.path.exists(full_path):
            print(f"[Warning] File not found: {rel_path}, skipping.")
            continue
        
        print(f"Processing & Merging: {rel_path}...")
        with open(full_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        # Find and render all mermaid blocks
        def replace_mermaid(match):
            diagram_code = match.group(1)
            file_url = get_kroki_diagram(diagram_code, screenshots_dir)
            if file_url:
                return f'<div class="diagram-image-container"><img src="{file_url}" alt="System Diagram" class="diagram-image" /></div>'
            else:
                return f'<pre><code class="language-text">{diagram_code}</code></pre>'

        md_text = mermaid_pattern.sub(replace_mermaid, md_text)

        # Convert md to html
        html_section = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
        
        html_content.append(f"""
        <div class="section-container">
            {html_section}
        </div>
        <div class="page-break"></div>
        """)

    # 4. Add Personal Engineering Takeaways (Wrap-up)
    engineering_reflections = f"""
    <div class="section-container">
        <h1>Personal Reflections & Lessons Learned</h1>
        <p>Developing <strong>PulseQueue</strong> was a profound exercise in systems design. Below are the key engineering takeaways and challenges solved during development:</p>

        <h3>1. The Subtleties of the Worker Heartbeat Timeout</h3>
        <p>Designing heartbeats requires balancing responsiveness with stability. If the heartbeat timeout is too short, temporary network latency will cause the scheduler to mark healthy workers as offline, leading to redundant job rescheduling (duplicate claims). If it is too long, crashed workers remain "active" in the DB, delaying job recovery. I configured a default timeout of 60 seconds with 5-second polling intervals, which provides a resilient buffer while ensuring stale tasks are recovered within a minute.</p>

        <h3>2. Solving Row-Level Contention</h3>
        <p>In early testing, database contention was a clear bottleneck when multiple worker threads polled the same queue. Implementing atomic updates using state constraints (e.g. `WHERE status = 'queued' AND id = ...`) prevents race conditions, but still results in "empty claims" (where a worker tries to claim a job but finds it already claimed by another). Transitioning to PostgreSQL's `SKIP LOCKED` query solved this by letting workers skip over currently locked rows entirely, maximizing concurrency throughput.</p>

        <h3>3. Graceful Shutdown & The Draining State</h3>
        <p>A major design goal was preventing orphan states when workers shut down. If a worker process is terminated (e.g., during deployments), killing threads abruptly leaves jobs stuck in `running` or `claimed` states, requiring scheduler scavenger sweeps. The implementation of OS signal trapping (SIGINT/SIGTERM) intercepts termination, immediately updates the worker status to `draining` (so no new jobs are polled), and allows active threads to cleanly finish. This dramatically improves overall cluster stability and prevents false-alarm alert triggers.</p>
    </div>
    <div class="page-break"></div>
    """
    html_content.insert(-1, engineering_reflections) # Place reflections before Next Steps

    # 5. Scan and Append Screenshots
    screenshot_files = []
    if os.path.exists(screenshots_dir):
        for f in sorted(os.listdir(screenshots_dir)):
            if f.lower().endswith((".png", ".jpg", ".jpeg")) and not f.startswith("diagram_"):
                screenshot_files.append(f)

    if screenshot_files:
        print("\nEmbedding Screenshots from docs/screenshots/...")
        html_content.append("<div class='section-container'><h1>System Operations Gallery</h1><p>The following screen captures demonstrate the live dashboard and APIs executing background jobs.</p>")
        for sf in screenshot_files:
            sf_path = os.path.join(screenshots_dir, sf)
            sf_url = "file:///" + sf_path.replace("\\", "/")
            caption = sf.split(".")[0].replace("_", " ").title()
            print(f"- Embedding screenshot: {sf} as '{caption}'")
            html_content.append(f"""
            <div class="screenshot-container">
                <h3>{caption}</h3>
                <img src="{sf_url}" alt="{caption}" />
            </div>
            """)
        html_content.append("</div><div class='page-break'></div>")

    # Build HTML Template with optimized CSS layout for diagrams
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>PulseQueue Submission - {name}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
            
            @page {{
                size: A4;
                margin: 2cm;
                @bottom-right {{
                    content: counter(page);
                }}
            }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                color: #172026;
                line-height: 1.6;
                font-size: 13px;
                background-color: #ffffff;
                margin: 0;
                padding: 0;
            }}

            a {{
                color: #0e7c7b;
                text-decoration: none;
                font-weight: 500;
            }}

            a:hover {{
                text-decoration: underline;
            }}

            .page-break {{
                page-break-before: always;
                break-before: page;
            }}

            /* Cover Page Styling */
            .cover-page {{
                height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                padding: 3cm 0;
                box-sizing: border-box;
            }}

            .logo {{
                font-size: 32px;
                font-weight: 800;
                background: #0e7c7b;
                color: #ffffff;
                width: 70px;
                height: 70px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 12px;
                margin-bottom: 2rem;
            }}

            .cover-page h1 {{
                font-size: 38px;
                font-weight: 800;
                color: #172026;
                margin: 0 0 10px 0;
                letter-spacing: -0.025em;
            }}

            .cover-page h2 {{
                font-size: 16px;
                font-weight: 500;
                color: #71717a;
                margin: 0 0 3rem 0;
                max-width: 500px;
            }}

            .divider {{
                width: 80px;
                height: 4px;
                background-color: #0e7c7b;
                margin-bottom: 3rem;
            }}

            .meta-container {{
                background-color: #edf2f4;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
                padding: 24px;
                width: 100%;
                max-width: 450px;
                text-align: left;
                margin-bottom: auto;
            }}

            .meta-item {{
                font-size: 13px;
                color: #2f3a40;
                margin-bottom: 12px;
            }}

            .meta-item:last-child {{
                margin-bottom: 0;
            }}

            .meta-item strong {{
                color: #172026;
                display: inline-block;
                width: 160px;
            }}

            .page-footer {{
                font-size: 11px;
                color: #a1a1aa;
                margin-top: 2rem;
            }}

            /* Standard Section styling */
            .section-container {{
                padding: 10px 0;
            }}

            h1, h2, h3, h4 {{
                color: #172026;
                font-weight: 700;
                letter-spacing: -0.02em;
                margin-top: 1.8rem;
                margin-bottom: 0.8rem;
            }}

            h1 {{
                font-size: 22px;
                border-bottom: 2px solid #edf2f4;
                padding-bottom: 8px;
                margin-top: 0;
            }}

            h2 {{
                font-size: 16px;
                margin-top: 2rem;
            }}

            h3 {{
                font-size: 14px;
            }}

            p, li {{
                color: #2f3a40;
                font-size: 13px;
                margin-bottom: 12px;
                text-align: justify;
            }}

            ul, ol {{
                margin-bottom: 16px;
                padding-left: 20px;
            }}

            li {{
                margin-bottom: 6px;
            }}

            /* Code and tables styling */
            code {{
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                font-size: 11px;
                background-color: #edf2f4;
                color: #c75000;
                padding: 2px 5px;
                border-radius: 4px;
            }}

            pre {{
                background-color: #edf2f4;
                border: 1px solid #e4e4e7;
                border-radius: 6px;
                padding: 12px 16px;
                overflow-x: auto;
                margin-bottom: 18px;
                break-inside: avoid;
            }}

            pre code {{
                background-color: transparent;
                color: #172026;
                padding: 0;
                border-radius: 0;
                font-size: 11px;
                line-height: 1.5;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                break-inside: avoid;
            }}

            th, td {{
                padding: 10px 12px;
                text-align: left;
                border-bottom: 1px solid #e4e4e7;
                font-size: 12px;
            }}

            th {{
                background-color: #edf2f4;
                font-weight: 600;
                color: #172026;
            }}

            tr:nth-child(even) {{
                background-color: #fafafa;
            }}

            /* Diagram Images (Optimized to fit on a single page) */
            .diagram-image-container {{
                margin: 15px auto;
                text-align: center;
                break-inside: avoid;
                page-break-inside: avoid;
                width: 100%;
            }}

            .diagram-image {{
                max-width: 100%;
                max-height: 20.5cm; /* Keeps the diagram fully on a single A4 page without breaking */
                width: auto;
                height: auto;
                display: block;
                margin: 0 auto;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
                background-color: #ffffff;
                padding: 16px;
                box-sizing: border-box;
                box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            }}

            /* Screenshots Gallery */
            .screenshot-container {{
                margin-bottom: 30px;
                break-inside: avoid;
                text-align: center;
            }}

            .screenshot-container h3 {{
                text-align: left;
                margin-bottom: 10px;
                color: #2f3a40;
            }}

            .screenshot-container img {{
                max-width: 100%;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }}
        </style>
    </head>
    <body>
        {"".join(html_content)}
    </body>
    </html>
    """

    temp_html_path = os.path.join(root_dir, "submission_temp.html")
    output_pdf_path = os.path.join(root_dir, "PulseQueue_Submission.pdf")

    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    print("\nTemporary HTML generated. Converting to PDF via Edge...")

    # Run Edge headless to print to PDF
    edge_executable = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    edge_args = [
        edge_executable,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={output_pdf_path}",
        temp_html_path
    ]

    try:
        subprocess.run(edge_args, check=True)
        print("-" * 60)
        print(" SUCCESS: Submission PDF created successfully with diagrams!")
        print(f" PDF Location: {output_pdf_path}")
        print("-" * 60)
    except Exception as e:
        print(f"\n[Error] Failed to execute Microsoft Edge to generate PDF: {e}")
        print("Please ensure Edge is installed, or try running Edge manually on submission_temp.html.")
    finally:
        # Clean up HTML file
        if os.path.exists(temp_html_path):
            try:
                os.remove(temp_html_path)
            except Exception:
                pass

if __name__ == "__main__":
    run()
