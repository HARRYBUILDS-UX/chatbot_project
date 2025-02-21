# Use an official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch separately (compatible CUDA version)
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .


# Expose the Streamlit port
EXPOSE 8501

# Start the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
