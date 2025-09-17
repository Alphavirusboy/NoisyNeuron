# NoisyNeuron 🎵# 🎧 NoisyNeuron - Professional Music Source Separation Platform



**Advanced AI-Powered Music Platform for Professional Audio Processing & Learning****NoisyNeuron** is a market-ready, professional AI-powered music source separation platform built with Django. Transform any music track into isolated stems with studio-quality results using industry-standard Spleeter technology.



A comprehensive Django-based platform that combines cutting-edge AI audio separation with interactive music education, designed for musicians, producers, and music enthusiasts.Perfect for musicians, producers, DJs, students, and audio professionals who need reliable stem separation with a modern, intuitive interface.



## 🌟 Key Features---



### 🎯 Professional Audio Separation## 🚀 Latest Updates (September 2025)

- **Spleeter 2.3.2 Integration**: Industry-standard AI model by Facebook Research

- **Multi-stem Separation**: Extract vocals, drums, bass, and other instruments✅ **Spleeter Integration** - Now powered by Facebook's industry-standard Spleeter for professional-grade separation  

- **High-Quality Output**: 16kHz optimized processing for professional results✅ **Python 3.10 Optimized** - Fully compatible and optimized for stability  

- **Real-time Progress**: WebSocket-powered live updates during processing✅ **4-Stem Separation** - Vocals, Drums, Bass, and Other instruments  

- **Multiple Format Support**: WAV, MP3, FLAC audio processing✅ **Production Ready** - Professional UI/UX designed for commercial use  

✅ **Market Ready** - Complete platform ready for deployment and monetization  

### 🎸 Interactive Instrument Learning

- **Comprehensive Instrument Guide**: Piano, guitar, violin, drums, and more---

- **Progressive Difficulty Levels**: Beginner to advanced techniques

- **Interactive Tutorials**: Step-by-step learning modules## 🌟 Key Features

- **Practice Exercises**: Structured skill-building activities

- **Progress Tracking**: Monitor your musical journey### 🎵 Professional Audio Processing

- **Spleeter 2.3.2** - Industry-standard AI source separation by Facebook Research

### 👤 Advanced User Management- **4-Stem Separation** - Vocals, Drums, Bass, Other (instruments/harmony)

- **Secure Authentication**: Email verification and password reset- **Multiple Formats** - Support for WAV, MP3, FLAC, OGG, M4A, AAC

- **User Profiles**: Personalized learning dashboards- **Real-time Progress** - Live processing updates with WebSocket technology

- **Premium Subscriptions**: Enhanced features for serious musicians- **High-Quality Output** - Studio-grade separation results

- **Project Management**: Save and organize your audio projects- **Batch Processing** - Handle multiple files efficiently



### 🧠 AI-Powered Music Theory### 🎓 Complete Music Learning Platform

- **Markov Chain Models**: Generate musical patterns and compositions- **Interactive Music Theory** - Comprehensive lessons and exercises

- **Theory Engine**: Advanced harmonic analysis and suggestions- **Instrument Learning** - Guitar, Piano, Drums, Bass tutorials

- **Pattern Recognition**: Identify musical structures and progressions- **Practice Tools** - Metronome, chord progressions, scale practice

- **Markov Chain Generation** - AI-powered music composition

## 🚀 Technology Stack- **Progress Tracking** - Detailed analytics and learning paths



### Backend### 👥 Professional User System

- **Django 5.2.6**: Modern Python web framework- **User Authentication** - Secure login/registration system

- **Python 3.10**: Optimized for audio processing libraries- **Premium Subscriptions** - Tiered pricing with advanced features

- **Spleeter 2.3.2**: Facebook Research's audio separation model- **Project Management** - Save, organize, and share separated tracks

- **TensorFlow 2.13.0**: Machine learning backend- **User Profiles** - Personalized dashboards and settings

- **Librosa 0.8.1**: Advanced audio analysis- **File Management** - Secure upload, processing, and download

- **Celery**: Asynchronous task processing

### 🎨 Modern Professional UI

### Frontend- **Responsive Design** - Works perfectly on desktop, tablet, and mobile

- **Modern CSS**: Custom properties and animations- **Professional Interface** - Clean, intuitive design suitable for commercial use

- **Responsive Design**: Mobile-first approach- **Real-time Updates** - Live progress indicators and notifications

- **JavaScript**: Interactive user experiences- **Accessibility** - WCAG compliant with keyboard navigation

- **WebSocket**: Real-time communication- **Modern CSS** - Custom properties, animations, and modern layouts



### Audio Processing---

- **NumPy 1.23.5**: Numerical computing

- **SciPy**: Scientific computing## 🛠 Tech Stack

- **Soundfile**: Audio I/O

- **Pydub**: Audio manipulation| Component      | Technology                                 |

|----------------|--------------------------------------------|

## 📦 Installation| **Backend**    | Django 5.2.6, Django REST Framework      |

| **Frontend**   | Modern HTML5, CSS3, JavaScript ES6+      |

### Prerequisites| **Audio AI**   | Spleeter 2.3.2, TensorFlow 2.13.0       |

- Python 3.10 (Required for Spleeter compatibility)| **Processing** | librosa 0.8.1, soundfile, pydub, numpy   |

- Git| **AI/ML**      | scikit-learn, music21, pandas            |

- Virtual environment support| **Real-time**  | Django Channels, WebSockets, Redis       |

| **Database**   | SQLite (dev), PostgreSQL (production)    |

### Quick Setup| **Queue**      | Celery, Redis                            |

| **Python**     | Python 3.10 (Optimized)                  |

1. **Clone the Repository**

   ```bash---

   git clone https://github.com/Alphavirusboy/NoisyNeuron.git

   cd NoisyNeuron## 🎯 Use Cases

   ```

- 🎵 **Music Production** - Extract stems for remixing and re-arrangement

2. **Create Virtual Environment**- 🎤 **Vocal Isolation** - Create karaoke tracks and a cappella versions

   ```bash- 🎚️ **Audio Mastering** - Isolate instruments for better mixing

   python3.10 -m venv .venv- 🎧 **Practice & Learning** - Play along with individual instrument tracks

   source .venv/bin/activate  # On macOS/Linux- 🎓 **Music Education** - Study arrangements and instrument techniques

   # or- 🔬 **Audio Research** - Analyze musical compositions and structures

   .venv\Scripts\activate     # On Windows- 💼 **Commercial Use** - Professional-grade platform ready for monetization

   ```

---

3. **Install Dependencies**

   ```bash## 🚀 Quick Start

   pip install --upgrade pip

   pip install -r requirements.txt### Prerequisites

   ```- **Python 3.10** (Required for Spleeter compatibility)

- Virtual environment (recommended)

4. **Install Spleeter**- Git

   ```bash- FFmpeg (for audio processing)

   pip install spleeter==2.3.2

   ```### Installation



5. **Database Setup**1. **Clone the repository**

   ```bash   ```bash

   python manage.py migrate   git clone https://github.com/Alphavirusboy/NoisyNeuron.git

   python manage.py createsuperuser   cd NoisyNeuron

   ```   ```



6. **Run the Server**2. **Create and activate virtual environment with Python 3.10**

   ```bash   ```bash

   python manage.py runserver   python3.10 -m venv .venv

   ```   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   ```

Visit `http://127.0.0.1:8000` to access the platform.

3. **Install dependencies**

## 🎵 Usage   ```bash

   pip install --upgrade pip

### Audio Separation   pip install -r requirements.txt

1. Upload your audio file (WAV, MP3, FLAC)   ```

2. Select separation model (2-stem or 4-stem)

3. Monitor real-time progress4. **Install Spleeter (if not included in requirements)**

4. Download separated tracks   ```bash

   pip install spleeter==2.3.2

### Instrument Learning   ```

1. Choose your instrument

2. Select difficulty level5. **Environment setup**

3. Follow interactive tutorials   Create a `.env` file in the project root:

4. Complete practice exercises   ```env

5. Track your progress   SECRET_KEY=your-secret-key-here

   DEBUG=True

### Premium Features   ALLOWED_HOSTS=localhost,127.0.0.1

- Advanced separation models   ```

- Unlimited processing time

- Priority queue access6. **Database setup**

- Extended file format support   ```bash

- Professional-grade exports   python manage.py migrate

   python manage.py collectstatic --noinput

## 🔧 Configuration   ```



### Environment Variables7. **Create media directories**

Create a `.env` file based on `.env.example`:   ```bash

   mkdir -p media/separated media/temp

```bash   ```

DEBUG=True

SECRET_KEY=your-secret-key8. **Run the development server**

DATABASE_URL=sqlite:///db.sqlite3   ```bash

SPLEETER_MODEL_PATH=path/to/spleeter/models   python manage.py runserver

```   ```



### Spleeter Models9. **Access the application**

The platform automatically downloads required models on first use:   Open your browser and navigate to `http://127.0.0.1:8000/`

- `spleeter:2stems-16kHz` (vocals/accompaniment)

- `spleeter:4stems-16kHz` (vocals/drums/bass/other)---



## 📂 Project Structure## 📁 Project Structure



``````

NoisyNeuron/NoisyNeuron/

├── accounts/           # User authentication & profiles├── accounts/              # User authentication & profiles

├── audio_processor/    # Spleeter integration & audio processing├── audio_processor/       # Core audio separation functionality

├── instruments/        # Interactive learning modules├── instruments/           # Music learning platform

├── music_theory/       # AI-powered theory engine├── markov_models/         # AI music generation

├── premium/           # Subscription & payment handling├── music_theory/          # Music theory engine

├── static/            # CSS, JS, images├── noisyneuron/          # Django project settings

├── templates/         # HTML templates├── static/               # Static files (CSS, JS, images)

├── media/             # User uploads & processed files├── templates/            # HTML templates

└── noisyneuron/       # Django project settings├── media/                # User uploads & processed files

```├── requirements.txt      # Python dependencies

├── manage.py            # Django management script

## 🌐 API Endpoints└── README.md           # This file

```

### Audio Processing

- `POST /api/audio/separate/` - Start audio separation---

- `GET /api/audio/status/<id>/` - Check processing status

- `GET /api/audio/download/<id>/` - Download results## 🎵 Audio Separation Usage



### User Management1. **Upload Audio File**

- `POST /api/auth/register/` - User registration   - Navigate to the audio separation page

- `POST /api/auth/login/` - User authentication   - Upload WAV, MP3, FLAC, OGG, M4A, or AAC files

- `GET /api/user/profile/` - User profile data   - Maximum file size: 100MB



### Instruments2. **Processing**

- `GET /api/instruments/` - List available instruments   - Spleeter automatically processes the file

- `GET /api/instruments/<id>/lessons/` - Get lessons for instrument   - Real-time progress updates via WebSocket

   - Processing time varies based on file length

## 🔍 Testing

3. **Download Results**

Run the test suite:   - Download individual stems (Vocals, Drums, Bass, Other)

```bash   - High-quality WAV format output

python manage.py test   - Preview stems before downloading

```

---

For specific app testing:

```bash## 🔧 Configuration

python manage.py test audio_processor

python manage.py test instruments### Spleeter Models

python manage.py test accountsThe platform uses Spleeter's pre-trained models:

```- **4stems-16kHz** - Separates into Vocals, Drums, Bass, Other

- **2stems-16kHz** - Separates into Vocals, Accompaniment (fallback)

## 🚀 Deployment

### Audio Settings

### Production Setup- **Sample Rate**: 44.1kHz (default)

1. Set `DEBUG=False` in settings- **Bit Depth**: 16-bit

2. Configure static file serving- **Format**: WAV (lossless output)

3. Set up proper database (PostgreSQL recommended)- **Channels**: Mono/Stereo (auto-detected)

4. Configure Celery with Redis/RabbitMQ

5. Set up nginx/Apache for file serving---



### Docker Support## 🚀 Deployment

```bash

docker build -t noisyneuron .### Production Setup

docker run -p 8000:8000 noisyneuron

```1. **Environment Variables**

   ```env

## 🤝 Contributing   SECRET_KEY=production-secret-key

   DEBUG=False

1. Fork the repository   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

2. Create a feature branch   DATABASE_URL=postgresql://user:pass@localhost/dbname

3. Make your changes   REDIS_URL=redis://localhost:6379/1

4. Add tests for new functionality   ```

5. Submit a pull request

2. **Static Files**

## 📄 License   ```bash

   python manage.py collectstatic --noinput

This project is licensed under the MIT License - see the LICENSE file for details.   ```



## 🔮 Roadmap3. **Database Migration**

   ```bash

### Upcoming Features   python manage.py migrate

- **Real-time Collaboration**: Multi-user project editing   ```

- **Mobile App**: Native iOS/Android applications

- **VST Plugin**: Direct integration with DAWs4. **Celery Worker** (for background processing)

- **AI Mastering**: Automated audio mastering   ```bash

- **Cloud Storage**: Secure project backup and sync   celery -A noisyneuron worker -l info

   ```

### Audio Processing Enhancements

- **Custom Model Training**: User-specific separation models### Docker Deployment

- **Advanced Preprocessing**: Noise reduction and enhancement

- **Format Conversion**: Professional audio format support```dockerfile

- **Batch Processing**: Multiple file processingFROM python:3.10-slim

WORKDIR /app

## 📞 SupportCOPY requirements.txt .

RUN pip install -r requirements.txt

- **Documentation**: [Wiki](https://github.com/Alphavirusboy/NoisyNeuron/wiki)COPY . .

- **Issues**: [GitHub Issues](https://github.com/Alphavirusboy/NoisyNeuron/issues)EXPOSE 8000

- **Email**: support@noisyneuron.comCMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

```

## 🏆 Acknowledgments

---

- **Spleeter Team**: Facebook Research for the audio separation models

- **Django Community**: For the robust web framework## 🧪 Testing

- **TensorFlow Team**: For machine learning infrastructure

- **Open Source Community**: For the amazing libraries and toolsRun the test suite:

```bash

---python manage.py test

```

**Made with ❤️ for the music community**

Run specific app tests:

*Transform your audio, elevate your music*```bash
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