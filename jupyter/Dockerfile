# Jupyter Development Environment — LARGE, allowed to contain PyTorch/YOLOv8/CUDA
# This container is NEVER deployed to production.
# Its only job: train models and export them to /workspace/exports/models/

FROM jupyter/datascience-notebook:latest

USER root

# System libs needed by OpenCV and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

USER $NB_UID

WORKDIR /workspace

# Copy Jupyter-specific requirements
COPY requirements.txt /tmp/jupyter-requirements.txt

# Install large ML stack — PyTorch CPU wheel by default (swap index-url for CUDA builds)
RUN pip install --no-cache-dir \
    torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /tmp/jupyter-requirements.txt

# Create export directory (shared volume will mount here)
RUN mkdir -p /workspace/exports/models /workspace/notebooks /workspace/data /workspace/scripts

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser", "--NotebookApp.token=zimagritrust"]
