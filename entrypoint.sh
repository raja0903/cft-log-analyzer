#!/bin/sh

# Default model (fallback)
MODEL=${OLLAMA_MODEL:-qwen3:0.6b}

echo "Using model: $MODEL"

# Start Ollama server in background
ollama serve &

# Wait for server to start
sleep 5

# Pull model if not present
if ! ollama list | grep -q "$MODEL"; then
    echo "Pulling model: $MODEL ..."
    ollama pull "$MODEL"
fi

# Keep container running
wait
