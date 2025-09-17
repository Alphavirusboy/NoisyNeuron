# 🎧 NoisyNeuron - Professional Music Source Separation Platform

**NoisyNeuron** is a market-ready, professional AI-powered music source separation platform built with Django. Transform any music track into isolated stems with studio-quality results using industry-standard Spleeter technology.

Perfect for musicians, producers, DJs, students, and audio professionals who need reliable stem separation with a modern, intuitive interface.

---

## 🚀 Latest Updates (September 2025)

✅ **Spleeter Integration** - Now powered by Facebook's industry-standard Spleeter for professional-grade separation  
✅ **Python 3.10 Optimized** - Fully compatible and optimized for stability  
✅ **4-Stem Separation** - Vocals, Drums, Bass, and Other instruments  
✅ **Production Ready** - Professional UI/UX designed for commercial use  
✅ **Market Ready** - Complete platform ready for deployment and monetization  

---

## 🌟 Key Features

### 🎵 Professional Audio Processing
- **Spleeter 2.3.2** - Industry-standard AI source separation by Facebook Research
- **4-Stem Separation** - Vocals, Drums, Bass, Other (instruments/harmony)
- **Multiple Formats** - Support for WAV, MP3, FLAC, OGG, M4A, AAC
- **Real-time Progress** - Live processing updates with WebSocket technology
- **High-Quality Output** - Studio-grade separation results
- **Batch Processing** - Handle multiple files efficiently

### 🎓 Complete Music Learning Platform
- **Interactive Music Theory** - Comprehensive lessons and exercises
- **Instrument Learning** - Guitar, Piano, Drums, Bass tutorials
- **Practice Tools** - Metronome, chord progressions, scale practice
- **Markov Chain Generation** - AI-powered music composition
- **Progress Tracking** - Detailed analytics and learning paths

### 👥 Professional User System
- **User Authentication** - Secure login/registration system
- **Premium Subscriptions** - Tiered pricing with advanced features
- **Project Management** - Save, organize, and share separated tracks
- **User Profiles** - Personalized dashboards and settings
- **File Management** - Secure upload, processing, and download

### 🎨 Modern Professional UI
- **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- **Professional Interface** - Clean, intuitive design suitable for commercial use
- **Real-time Updates** - Live progress indicators and notifications
- **Accessibility** - WCAG compliant with keyboard navigation
- **Modern CSS** - Custom properties, animations, and modern layouts

---

## 🛠 Tech Stack

| Component      | Technology                                 |
|----------------|--------------------------------------------|
| **Backend**    | Django 5.2.6, Django REST Framework      |
| **Frontend**   | Modern HTML5, CSS3, JavaScript ES6+      |
| **Audio AI**   | Spleeter 2.3.2, TensorFlow 2.13.0       |
| **Processing** | librosa 0.8.1, soundfile, pydub, numpy   |
| **AI/ML**      | scikit-learn, music21, pandas            |
| **Real-time**  | Django Channels, WebSockets, Redis       |
| **Database**   | SQLite (dev), PostgreSQL (production)    |
| **Queue**      | Celery, Redis                            |
| **Python**     | Python 3.10 (Optimized)                  |

---

## 🎯 Use Cases

- 🎵 **Music Production** - Extract stems for remixing and re-arrangement
- 🎤 **Vocal Isolation** - Create karaoke tracks and a cappella versions
- 🎚️ **Audio Mastering** - Isolate instruments for better mixing
- 🎧 **Practice & Learning** - Play along with individual instrument tracks
- 🎓 **Music Education** - Study arrangements and instrument techniques
- 🔬 **Audio Research** - Analyze musical compositions and structures
- 💼 **Commercial Use** - Professional-grade platform ready for monetization

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10** (Required for Spleeter compatibility)
- Virtual environment (recommended)
- Git
- FFmpeg (for audio processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Alphavirusboy/NoisyNeuron.git
   cd NoisyNeuron
   ```

2. **Create and activate virtual environment with Python 3.10**
   ```bash
   python3.10 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install Spleeter (if not included in requirements)**
   ```bash
   pip install spleeter==2.3.2
   ```

5. **Environment setup**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

6. **Database setup**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

7. **Create media directories**
   ```bash
   mkdir -p media/separated media/temp
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000/`

---

## 📁 Project Structure

```
NoisyNeuron/
├── accounts/              # User authentication & profiles
├── audio_processor/       # Core audio separation functionality
├── instruments/           # Music learning platform
├── markov_models/         # AI music generation
├── music_theory/          # Music theory engine
├── noisyneuron/          # Django project settings
├── static/               # Static files (CSS, JS, images)
├── templates/            # HTML templates
├── media/                # User uploads & processed files
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
└── README.md           # This file
```

---

## 🎵 Audio Separation Usage

1. **Upload Audio File**
   - Navigate to the audio separation page
   - Upload WAV, MP3, FLAC, OGG, M4A, or AAC files
   - Maximum file size: 100MB

2. **Processing**
   - Spleeter automatically processes the file
   - Real-time progress updates via WebSocket
   - Processing time varies based on file length

3. **Download Results**
   - Download individual stems (Vocals, Drums, Bass, Other)
   - High-quality WAV format output
   - Preview stems before downloading

---

## 🔧 Configuration

### Spleeter Models
The platform uses Spleeter's pre-trained models:
- **4stems-16kHz** - Separates into Vocals, Drums, Bass, Other
- **2stems-16kHz** - Separates into Vocals, Accompaniment (fallback)

### Audio Settings
- **Sample Rate**: 44.1kHz (default)
- **Bit Depth**: 16-bit
- **Format**: WAV (lossless output)
- **Channels**: Mono/Stereo (auto-detected)

---

## 🚀 Deployment

### Production Setup

1. **Environment Variables**
   ```env
   SECRET_KEY=production-secret-key
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DATABASE_URL=postgresql://user:pass@localhost/dbname
   REDIS_URL=redis://localhost:6379/1
   ```

2. **Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Database Migration**
   ```bash
   python manage.py migrate
   ```

4. **Celery Worker** (for background processing)
   ```bash
   celery -A noisyneuron worker -l info
   ```

### Docker Deployment

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

---

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

Run specific app tests:
```bash
python manage.py test audio_processor
python manage.py test accounts
python manage.py test instruments
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📋 Requirements

### System Requirements
- Python 3.10+
- FFmpeg
- Redis (for real-time features)
- PostgreSQL (production)

### Python Dependencies
- Django 5.2.6
- Spleeter 2.3.2
- TensorFlow 2.13.0
- librosa 0.8.1
- soundfile
- pydub
- numpy
- scipy
- celery
- redis
- django-channels

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Spleeter** by Facebook Research for audio source separation
- **Django** framework for robust web development
- **TensorFlow** for machine learning capabilities
- **librosa** for audio analysis tools

---

## 📞 Support & Contact

- **GitHub Issues**: [Report bugs and feature requests](https://github.com/Alphavirusboy/NoisyNeuron/issues)
- **Documentation**: [Wiki](https://github.com/Alphavirusboy/NoisyNeuron/wiki)
- **Email**: support@noisyneuron.com

---

## 🌟 Show Your Support

If you find NoisyNeuron useful, please ⭐ star this repository and share it with fellow musicians and developers!

---

**NoisyNeuron** - *Professional Music Source Separation Made Simple* 🎵