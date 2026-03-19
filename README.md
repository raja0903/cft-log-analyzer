# AI Log Analyzer

An intelligent log analysis tool powered by Flask and Ollama that helps diagnose file transfer issues by analyzing log files, error codes, and debug information. The application uses machine learning (TF-IDF and cosine similarity) to match error messages and generates AI-powered troubleshooting suggestions.

## Features

- **Intelligent Log Parsing**: Automatically parses log files and identifies error codes, warnings, and fatal errors
- **Knowledge Base Matching**: Uses cosine similarity to match error messages against a comprehensive knowledge base
- **AI-Powered Suggestions**: Leverages Ollama (LLaMA) to generate troubleshooting steps and possible causes
- **Multiple File Support**: Process multiple log files simultaneously
- **Debug File Analysis**: Analyzes debug files to extract DIAGI and DIAGP codes
- **Web Interface**: User-friendly Flask-based web interface for file uploads and results visualization
- **Secure File Handling**: Implements secure filename handling and content validation

## Prerequisites

Before installing and running this application, ensure you have the following installed:

### Required Software

- **Python 3.9 or higher**
  - Download from: https://www.python.org/downloads/
  - During installation, check "Add Python to PATH"

- **Ollama** (for AI suggestions)
  - Download from: https://ollama.ai/download
  - Or install via command line:
    ```bash
    # Linux/macOS
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Windows
    winget install Ollama.Ollama
    ```

- **Git** (optional, for cloning the repository)
  - Download from: https://git-scm.com/downloads

### Ollama Model Setup

After installing Ollama, download and run the LLaMA model:

```bash
# Pull the recommended model (qwen3:0.6b)
ollama pull qwen3:0.6b

# Verify the model is available
ollama list
```

**Note**: You can use other LLaMA models (e.g., `llama3.2:3b`, `llama3.1:8b`). Update the `OLLAMA_MODEL` environment variable accordingly in the `.env` file.

## Installation

### Step 1: Clone or Download the Repository

**Option A: Clone using Git**
```bash
git clone https://git-ext.ecd.axway.com/gss-noida/ai/log-analyzer.git
cd log-analyzer
```

**Option B: Download ZIP**
1. Download the repository as a ZIP file
2. Extract it to your desired location
3. Navigate to the extracted directory

### Step 2: Create Virtual Environment (Recommended)

Creating a virtual environment isolates the project dependencies:

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- Flask 3.0.0+ (Web framework)
- python-dotenv 1.0.0+ (Environment variable management)
- requests 2.31.0+ (HTTP client for Ollama API)
- scikit-learn 1.3.0+ (Machine learning for similarity matching)
- Werkzeug 3.0.0+ (Utilities for Flask)

### Step 4: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   # Windows
   copy .env.example .env
   
   # Linux/macOS
   cp .env.example .env
   ```

2. Edit the `.env` file to configure the application:
   ```env
   # Ollama Configuration
   OLLAMA_URL=http://127.0.0.1:11434/api/generate
   OLLAMA_MODEL=llama3.2:1b

   # Analysis Thresholds
   SIMILARITY_THRESHOLD=0.3
   DIAGI_REMOTE_THRESHOLD=500

   # Flask Configuration
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   FLASK_DEBUG=False
   ```

**Configuration Options:**
- `OLLAMA_URL`: URL of the Ollama API endpoint (default: `http://127.0.0.1:11434/api/generate`)
- `OLLAMA_MODEL`: Name of the Ollama model to use (default: `llama3.2:1b`)
- `SIMILARITY_THRESHOLD`: Minimum similarity score (0.0-1.0) for matching error messages (default: `0.3`)
- `DIAGI_REMOTE_THRESHOLD`: DIAGI code value above which errors are considered "Remote" (default: `500`)
- `FLASK_HOST`: Host address to bind the Flask server (default: `0.0.0.0`)
- `FLASK_PORT`: Port number for the Flask server (default: `5000`)
- `FLASK_DEBUG`: Enable Flask debug mode (default: `False`)

### Step 5: Verify Required Knowledge Base Files

Ensure the following knowledge base files exist in the project root:
- `diagi_knowledgebase.json` - Contains DIAGI code information and events
- `knowledgebase.json` - Contains error code mappings and explanations

**Important**: These files are required for the application to function. If they are missing, the application will fail to process files.

## Running the Application

### Step 1: Start Ollama Service

Make sure Ollama is running in the background:

**Windows:**
```cmd
# Start Ollama in a separate terminal window
ollama serve
```

**Linux/macOS:**
```bash
# Start Ollama in the background
ollama serve &
```

Or run Ollama normally (it starts the server automatically):
```bash
ollama run qwen3:0.6b
```

### Step 2: Start the Flask Application

With your virtual environment activated:

```bash
python AI_app.py
```

You should see output similar to:
```
INFO - Starting AI Log Analyzer on 0.0.0.0:5000
INFO -  * Running on http://0.0.0.0:5000
```

### Step 3: Access the Web Interface

Open your web browser and navigate to:

- **Local access**: http://localhost:5000
- **Network access**: http://YOUR_IP_ADDRESS:5000

## Usage

### 1. Upload Files

1. Enter the **IDT (Transfer ID)** you want to analyze
2. Upload the **debug file** (required)
3. Upload one or more **log files** (required)
4. Click **Analyze**

### 2. View Results

The application will display:
- **DIAGI Information**: DIAGI code, type (Local/Remote), event description
- **AI Suggestions**: AI-generated troubleshooting steps and possible causes
- **Error Analysis**: List of errors found in log files with:
  - Error code
  - Severity level (warning/error/fatal)
  - Error message
  - Closest matching knowledge base entry
  - Explanation and consequence
- **Log Statistics**: Total number of logs processed and errors found

### 3. Interpret Results

- **DIAGI Code**: Diagnostic code indicating the type of transfer issue
- **AI Suggestions**: Review the AI-generated troubleshooting steps and consider implementing them
- **Error Matches**: Check error codes against the knowledge base for standard solutions
- **Similarity Score**: Higher scores indicate better matches between log messages and knowledge base entries

## File Upload Requirements

- **Debug File**: Required text file containing debug information with transfer ID details
- **Log Files**: Required text files containing log entries in the format:
  ```
  MM/DD/YY HH:MM:SS XXXXXE Error message here
  ```
  Where:
  - `MM/DD/YY`: Date
  - `HH:MM:SS`: Time
  - `XXXXX`: Error code prefix
  - `E`: Error level (W=Warning, E=Error, F=Fatal)
- **File Size**: Maximum 100MB per file
- **Encoding**: UTF-8 or Latin-1

## Troubleshooting

### Application Won't Start

**Issue**: Module import errors
```
ModuleNotFoundError: No module named 'flask'
```
**Solution**: Ensure you've activated the virtual environment and installed dependencies:
```bash
pip install -r requirements.txt
```

### Ollama Connection Errors

**Issue**: "Ollama error: Connection failed"
**Solutions**:
1. Ensure Ollama is running: `ollama serve`
2. Check if Ollama is accessible: `curl http://127.0.0.1:11434/api/generate`
3. Verify the model is installed: `ollama list`
4. Check `OLLAMA_URL` in `.env` file

**Issue**: "Ollama error: Timeout"
**Solutions**:
1. Ensure you have enough RAM for the model
2. Try a smaller model (e.g., `llama3.2:1b` instead of `llama3.1:8b`)
3. Increase timeout in `AI_app.py` (line 113) if needed

### File Upload Errors

**Issue**: "File is required" or "No valid log files provided"
**Solution**: Ensure you're uploading valid text files with the correct format

**Issue**: "Unable to decode file content"
**Solution**: Ensure files are text-based (UTF-8 or Latin-1 encoded), not binary files

### Knowledge Base Errors

**Issue**: "Required knowledge base file missing"
**Solution**: Ensure `diagi_knowledgebase.json` and `knowledgebase.json` exist in the project root directory

### Port Already in Use

**Issue**: "Address already in use" or similar error
**Solution**: Change the port in `.env` file:
```env
FLASK_PORT=5001
```
Or stop the process using port 5000:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:5000 | xargs kill -9
```

## Project Structure

```
AI_log_analyser_final_CFT/
├── AI_app.py                      # Main Flask application
├── requirements.txt               # Python dependencies
├── .env                           # Environment configuration (create from .env.example)
├── .env.example                   # Example environment configuration
├── .gitignore                     # Git ignore rules
├── diagi_knowledgebase.json       # DIAGI code knowledge base
├── knowledgebase.json             # Error code knowledge base
├── templates/                     # HTML templates
│   ├── upload.html                # File upload interface
│   └── results.html               # Results display interface
└── README.md                      # This file
```

## Development

### Running in Debug Mode

Enable debug mode for development:
```env
FLASK_DEBUG=True
```

This will enable:
- Auto-reload on code changes
- Detailed error messages
- Interactive debugger

### Viewing Logs

Application logs are written to `ai_app.log` and also printed to the console.

### Adding Custom Knowledge Base Entries

Edit `knowledgebase.json` or `diagi_knowledgebase.json` to add custom error codes or DIAGI entries. Follow the existing JSON structure.

## Security Considerations

- File uploads are limited to 100MB per file
- Filenames are sanitized using `secure_filename()`
- Only text files are accepted (UTF-8/Latin-1 encoding)
- Environment variables should not be committed to version control
- Debug mode should be disabled in production

## Performance Tips

- Use smaller LLaMA models (e.g., `llama3.2:1b`) for faster AI responses
- Adjust `SIMILARITY_THRESHOLD` to balance precision vs. recall
- Process multiple log files at once for batch analysis
- Ensure adequate RAM for Ollama (recommended: 8GB+ for llama3.2:1b)

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software for internal use.

## Support

For issues or questions:
- Check the Troubleshooting section above
- Review application logs in `ai_app.log`
- Contact the development team

## Acknowledgments

- **Flask**: Web framework
- **Ollama**: Local LLM runtime
- **scikit-learn**: Machine learning library for similarity matching
- **LLaMA**: Meta's open-source language model

---

**Version**: 1.0.0  
**Last Updated**: March 2026