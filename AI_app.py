from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import re
import json
import requests
import os
import logging
from io import StringIO
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Security: Max file upload size (100MB)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Configuration from environment variables
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434/api/generate')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.3'))
DIAGI_REMOTE_THRESHOLD = int(os.getenv('DIAGI_REMOTE_THRESHOLD', '500'))

# Knowledge base file paths
KB_DIR = Path(__file__).parent
DIAGI_KB_PATH = KB_DIR / 'diagi_knowledgebase.json'
KB_PATH = KB_DIR / 'knowledgebase.json'


def safe_decode(content: bytes, default_encoding: str = 'utf-8') -> str:
    """Safely decode file content with fallback"""
    try:
        return content.decode(default_encoding)
    except UnicodeDecodeError:
        try:
            return content.decode('latin-1')
        except Exception as e:
            logger.error(f"Failed to decode file content: {e}")
            raise ValueError("Unable to decode file content. Please ensure files are text-based.")


def load_knowledge_bases():
    """Load knowledge base files with proper error handling"""
    try:
        with open(DIAGI_KB_PATH, 'r', encoding='utf-8') as f:
            diagi_kb = json.load(f)
    except FileNotFoundError:
        logger.error(f"DIAGI knowledge base not found: {DIAGI_KB_PATH}")
        raise FileNotFoundError(f"Required knowledge base file missing: diagi_knowledgebase.json")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in DIAGI knowledge base: {e}")
        raise ValueError(f"Invalid knowledge base format: {e}")

    try:
        with open(KB_PATH, 'r', encoding='utf-8') as f:
            kb = json.load(f)
            kb_errors = []
            kb_messages = []
            for entry in kb:
                error_key = entry.get("V23 format V24 format Error", "")
                if error_key:
                    parts = error_key.split()
                    if parts:
                        kb_errors.append(parts[0])
                        kb_messages.append(error_key)
    except FileNotFoundError:
        logger.error(f"Knowledge base not found: {KB_PATH}")
        raise FileNotFoundError(f"Required knowledge base file missing: knowledgebase.json")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in knowledge base: {e}")
        raise ValueError(f"Invalid knowledge base format: {e}")

    return diagi_kb, kb, kb_errors, kb_messages


def parse_log(log_line):
    match = re.match(r"(\d{2}/\d{2}/\d{2} \S+)\s+(\w+?)([WEF])\s+(.*)", log_line)
    if not match:
        return None
    level_mapping = {'W': 'warning', 'E': 'error', 'F': 'fatal'}
    return {
        "error_code": match.group(2) + match.group(3),
        "level": level_mapping[match.group(3)],
        "message": match.group(4).strip()
    }


def find_closest_message(message, kb_messages):
    if not kb_messages:
        return None

    vectorizer = TfidfVectorizer().fit_transform([message] + kb_messages)
    similarities = cosine_similarity(vectorizer[0:1], vectorizer[1:]).flatten()
    best_match_index = similarities.argmax()
    return kb_messages[best_match_index] if similarities[best_match_index] > SIMILARITY_THRESHOLD else None


def generate_ai_suggestion(event_description: str):
    """Generate AI suggestions using Ollama"""
    logger.info("="*60)
    logger.info("AI Suggestion Generation Started")
    logger.info(f"Using Ollama provider - URL: {OLLAMA_URL}, Model: {OLLAMA_MODEL}")
    logger.info("="*60)

    if not event_description.strip():
        logger.warning("Empty event description provided to generate_ai_suggestion")
        return "No event description provided"

    prompt = f"""
    As a senior file transfer engineer, suggest 3 possible causes for:
    {event_description}. Do not analyse the words DIAGP and DIAGC. You can suggest commands to check if actually it is not working.

    Keep answers technical and specific.</s>
    Generate troubleshooting steps:</s>
    """

    try:
        logger.info("Initiating Ollama API request...")
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 200,
                    "stop": ["</s>"]
                }
            },
            timeout=240
        )
        logger.info(f"Ollama response received - Status Code: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        suggestion = result["response"].split("</s>")[-1].strip()
        logger.info(f"Ollama suggestion generated successfully - Length: {len(suggestion)} chars")
        logger.info("="*60)
        return suggestion
    except requests.exceptions.Timeout as e:
        logger.error(f"Ollama Timeout Error: {str(e)}")
        logger.info("="*60)
        return f"Ollama error: Timeout - {str(e)}"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Ollama Connection Error: {str(e)}")
        logger.info("="*60)
        return f"Ollama error: Connection failed - {str(e)}"
    except Exception as e:
        logger.error(f"Ollama Error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.info("="*60)
        return f"Ollama error: {str(e)}"


def process_files(log_files, debug_content, idt_to_search):
    results = {
        'files': {},
        'diag_info': {},
        'total_errors': 0,
        'total_logs': 0,
        'ai_available': True,
        'ai_error': None
    }

    # Load knowledge bases with proper error handling
    try:
        diagi_kb, kb, kb_errors, kb_messages = load_knowledge_bases()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Knowledge base error: {str(e)}")
        results['ai_available'] = False
        results['ai_error'] = f"Configuration error: {str(e)}"
        return results

    # Process each log file
    for log_file in log_files:
        filename = log_file['name']
        log_content = log_file['content']

        results['files'][filename] = {
            'errors': [],
            'raw_logs': []
        }

        for line in StringIO(log_content):
            if (line := line.strip()) and idt_to_search in line:
                results['files'][filename]['raw_logs'].append(line)
                results['total_logs'] += 1

                if parsed := parse_log(line):
                    if parsed['error_code'] in kb_errors:
                        closest = find_closest_message(parsed['message'], kb_messages)
                        entry = next((e for e in kb if e.get("V23 format V24 format Error", "").startswith(parsed['error_code'])), None)
                        results['files'][filename]['errors'].append({
                            'error_code': parsed['error_code'],
                            'level': parsed['level'],
                            'message': parsed['message'],
                            'closest_message': closest or 'No close match',
                            'explanation': entry.get("Explanation", "") if entry else "",
                            'consequence': entry.get("Consequence", "") if entry else ""
                        })
                        results['total_errors'] += 1

        # Remove files that have no matching log lines
        if not results['files'][filename]['raw_logs']:
            del results['files'][filename]
            logger.info(f"File '{filename}' removed from results: No matching log lines found")

    # Process debug info
    diag_data = {}
    current_idt = None
    for line in StringIO(debug_content):
        line = line.strip()
        if line.startswith("Transfer id.                      IDT        = "):
            current_idt = line.split("=")[1].strip()
        elif current_idt == idt_to_search:
            if "DIAGI" in line:
                if match := re.search(r"DIAGI\s*=\s*(\d+)", line):
                    diag_data["DIAGI"] = int(match.group(1))
            elif "DIAGP" in line:
                diag_data["DIAGP"] = line.split("=", 1)[1].strip()

    if diag_data.get("DIAGI"):
        logger.info("="*60)
        logger.info(f"DIAGI Code Found: {diag_data['DIAGI']}")
        logger.info("="*60)

        entry = next((e for e in diagi_kb if str(e.get("DIAGI Code", "")) == str(diag_data["DIAGI"])), None)
        event = ". ".join(entry["Events"]) if entry and isinstance(entry.get("Events"), list) else entry.get("Events", "")

        logger.info(f"Event description extracted (first 100 chars): {event[:100]}...")
        logger.info(f"Knowledge base entry found: {'Yes' if entry else 'No'}")

        # Generate AI suggestions
        logger.info("Calling AI to generate suggestions...")
        ai_suggestion = generate_ai_suggestion(event)

        # Check if AI generation failed - use precise error message patterns
        # Only flag actual API errors, not troubleshooting advice
        error_prefixes = [
            "Ollama error:",
            "No event description provided",
            "API connection failed",
            "Connection error:",
            "Timeout error:",
            "HTTP Error:",
            "Request failed:",
            "Unexpected error:"
        ]

        logger.info("Checking for AI failure indicators...")
        ai_failed = any(ai_suggestion.lower().startswith(prefix.lower()) for prefix in error_prefixes)

        if ai_failed:
            logger.error(f"AI generation FAILED - AI marked as unavailable")
            logger.error(f"Error message: {ai_suggestion[:200]}...")
            results['ai_available'] = False
            results['ai_error'] = ai_suggestion
            diag_data['ai_suggestions'] = None
        else:
            logger.info(f"AI generation SUCCEEDED - AI marked as available")
            logger.info(f"Suggestion length: {len(ai_suggestion)} chars")
            results['ai_available'] = True
            results['ai_error'] = None
            diag_data['ai_suggestions'] = ai_suggestion

        logger.info("="*60)
        logger.info(f"AI Availability Status: {'Available' if results['ai_available'] else 'Not Available'}")
        if not results['ai_available']:
            logger.error(f"AI Error: {results['ai_error'][:200]}...")
        logger.info("="*60)

        diag_data.update({
            'diagi_type': "Remote" if diag_data["DIAGI"] > DIAGI_REMOTE_THRESHOLD else "Local",
            'event': event,
            'consequence': entry.get("Consequences", "") if entry else ""
        })

    results['diag_info'] = diag_data
    return results


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        idt = request.form.get('idt', '').strip()
        log_files = request.files.getlist('log_files')
        debug_file = request.files.get('debug_file')

        # Validate required fields
        if not debug_file or not debug_file.filename:
            return render_template('upload.html', error="Debug file is required.")

        if not log_files or all(not lf.filename for lf in log_files):
            return render_template('upload.html', error="At least one log file is required.")

        try:
            # Prepare log files data
            log_files_data = []
            for log_file in log_files:
                if log_file.filename:
                    # Secure the filename
                    secure_name = secure_filename(log_file.filename)
                    try:
                        content = safe_decode(log_file.read())
                        log_files_data.append({
                            'name': secure_name,
                            'content': content
                        })
                    except ValueError as e:
                        return render_template('upload.html', error=str(e))

            if not log_files_data:
                return render_template('upload.html', error="No valid log files provided.")

            # Process debug file
            try:
                debug_content = safe_decode(debug_file.read())
            except ValueError as e:
                return render_template('upload.html', error=str(e))

            # Process files
            results = process_files(
                log_files_data,
                debug_content,
                idt
            )
            return render_template('results.html', results=results, idt=idt)

        except Exception as e:
            logger.exception("Error processing files")
            return render_template('upload.html', error="An error occurred while processing your files. Please check the file formats and try again.")

    return render_template('upload.html')


if __name__ == '__main__':
    # Bind to 0.0.0.0 for corporate network access
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting AI Log Analyzer on {host}:{port}")
    app.run(debug=debug, host=host, port=port)
