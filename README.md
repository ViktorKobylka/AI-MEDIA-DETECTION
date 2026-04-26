# AI Deepfake Detection System

Final Year Project - AI-powered deepfake detection with continual learning and dual-detector architecture.

## Overview

A production-ready web application that detects AI-generated images and videos using an ensemble of vision transformers and continual learning for autonomous model improvement.

**Live Demo:** [aimediadetection.com](https://www.aimediadetection.com)
**Video Demonstration:** [ViktorKobylkaScreencast.mp4](https://atlantictu-my.sharepoint.com/:v:/g/personal/g00425163_atu_ie/IQA2JhLLoPgnQ77P5frNf8uAAU6U1W_yBmOeFf9cMoTs8HY?e=GkNHHF)  
**Training Dataset (14,001 images):** [dataset_orig](https://atlantictu-my.sharepoint.com/:f:/g/personal/g00425163_atu_ie/IgB2w1Vmcj8oQakS5jky9EZpARVmNPhhrycsrPEF-AlBnss?e=WT2A3n) | **Validation Dataset (250 images):** [dataset_val](https://atlantictu-my.sharepoint.com/:f:/g/personal/g00425163_atu_ie/IgD8-qTcQpaiTqg2S6O_qssQAVe8Fu8deD4iOCabK5xK8Ho?e=LSz7O6)

## Architecture

### Dual-Detector System
- **MobileNetV4** (Custom trained, 82% F1)
  - Real Accuracy: 71%
  - Fake Accuracy: 85%
- **SightEngine API** (Commercial baseline)

### Continual Learning Pipeline
- **Experience Replay:** 80% original dataset + 100% new user data
- **Quality Control:** 2% degradation tolerance with automatic rollback
- **Autonomous Retraining:** Scheduled daily at 3:00 AM
- **Round Merging:** Every 5 rounds, user data integrated into base dataset

## Dataset Sources

### Training Dataset (14,001 images)
- **OpenFake** (ComplexDataLab, 2025) - [arXiv:2509.09495](https://arxiv.org/abs/2509.09495)
- **MS COCOAI** (2026) - [arXiv:2601.00553](https://arxiv.org/abs/2601.00553)
- **UTKFace** (Zhang et al., CVPR 2017) - (https://susanqq.github.io/UTKFace/)
- **Pexels** - (https://www.pexels.com/)

### Cross-Dataset Evaluation (250 images)
- **ehristoforu/midjourney-images (Midjourney v5/v6)** - (https://huggingface.co/datasets/ehristoforu/midjourney-images)
- **BaiqiL/GenAI-Bench (DALL-E 3, MJ v6, SDXL)** - [arXiv:2406.13743](https://arxiv.org/abs/2406.13743)
- **Pexels** - (https://www.pexels.com/)

### AI Generators Covered
Stable Diffusion (1.5/2.1/XL/3.5), Flux (1.0/1.1), Midjourney (v6/v7), DALL-E 3, GPT Image 1, Ideogram 3.0, Imagen (3/4), Grok 2, HiDream, Chroma

## Features

-  **Dual-Detector Consensus** - Hybrid approach combining custom model + commercial API
-  **Continual Learning** - Autonomous model improvement with experience replay
-  **Content-Addressable Storage** - SHA-256 deduplication for efficient caching
-  **Real-time Statistics** - MongoDB-backed analytics dashboard
-  **Production Deployment** - SSL, domain, systemd services, auto-reload

## 🛠️ Tech Stack

**Backend:**
- Flask + Gunicorn
- PyTorch (MobileNetV4)
- MongoDB Atlas
- OpenCV (video processing)

**Frontend:**
- React 18
- Bootstrap 5
- Recharts (visualization)

**Infrastructure:**
- DigitalOcean (Backend - $48/mo CPU-optimized)
- Vercel (Frontend - Free tier)
- SSL
- Nginx reverse proxy

## Installation

### Prerequisites
- Python 3.12+
- Node.js 20+
- MongoDB
- 8GB RAM (for training)

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
SIGHTENGINE_API_USER=your_user
SIGHTENGINE_API_SECRET=your_secret
MONGO_URI=mongodb://localhost:27017
EOF

# Run development server
python app.py
```

### Frontend Setup

```bash
cd frontend
npm install

# Create .env file
echo "REACT_APP_API_URL=http://localhost:5000" > .env

# Run development server
npm start
```

## Academic Context

**Project Type:** Final Year Project (FYP)  
**Key Contributions:**
- Production-ready deployment of pretrained models
- Continual learning pipeline with quality control
- Dual-detector ensemble for improved reliability
- Content-addressable caching for performance optimization

## Evaluation

**Validation Set Performance:**
- MobileNetV4: 82% F1, 71% Real Acc, 85% Fake Acc
- Cross-dataset generalization tested on unseen generators
- Quality control prevents deployment of degraded models

## Acknowledgements

- **[MobileNetV4](https://arxiv.org/abs/2404.10518)** - Qin et al., 2024
- **[OpenFake](https://arxiv.org/abs/2509.09495)** - Livernoche et al., 2025
- **[SightEngine](https://sightengine.com)** - Commercial AI detection API
  
