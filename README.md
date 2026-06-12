🎙️ Telegram Voice to Video Bot

Turn voice recordings into videos automatically using Telegram.

✨ Features

- 🎤 Send a WAV voice recording to Telegram Saved Messages
- 🤖 Automatically detects new audio files
- 📝 Generates subtitles using Whisper AI
- 🔊 Enhances audio quality
- 🖼️ Creates videos using images from your local photo library
- 🎬 Adds transitions and visual effects
- 📤 Sends the finished MP4 video back to Telegram
- 💾 Saves generated videos locally

🚀 How It Works

1. 🎤 Send a WAV file to Telegram Saved Messages
2. 📥 The bot downloads the audio
3. 🧠 Whisper AI transcribes the speech
4. 🖼️ Images are selected from your photo library
5. 🎬 A vertical video is created automatically
6. 📝 Subtitles are added
7. 📤 The finished MP4 is sent back to Telegram

📋 Requirements

- 🐍 Python 3.10+
- 🎞️ FFmpeg
- 🖋️ ImageMagick
- 🔑 Telegram API ID & API Hash
- 🧠 Whisper AI Model

⚙️ Installation

pip install -r requirements.txt

Add your Telegram API credentials to the script before running.

▶️ Run

python Instagram-reel-editor-automation.py

📁 Output

- 🎬 Generated videos are saved locally
- 📤 Videos are automatically uploaded to Telegram Saved Messages
- 📊 Processing history is stored in a local database

🛠️ Tech Stack

- 🐍 Python
- 📱 Telethon
- 🧠 OpenAI Whisper
- 🎞️ MoviePy
- 🎵 Pydub
- 🔊 NoiseReduce
- 📷 OpenCV

📜 License

MIT License

⭐ If you find this project useful, consider giving it a star.
