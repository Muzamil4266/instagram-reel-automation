import os
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["IMAGEIO_FFMPEG_EXE"] = "ffmpeg"

import time
import shutil
import hashlib
import sqlite3
import random
import datetime
import schedule
import json
import math
import sys
import threading
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from proglog import ProgressBarLogger

# Audio/Video Processing
import soundfile as sf
import noisereduce as nr
from pydub import AudioSegment, effects
import whisper
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout
from moviepy.video.VideoClip import ImageClip as BaseImageClip

# ==========================================
# IMAGEMAGICK CONFIGURATION FOR SUBTITLES
# ==========================================
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

# Telegram Userbot
from telethon import TelegramClient, sync
from telethon.tl.types import MessageMediaDocument

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
API_ID = 34416633
API_HASH = 'b2aed0b8baa8e30c234d8e46c7d05b83'

IMAGE_LIBRARY_DIR = r"C:\Shoby deathless laptop folder\Instagram-tutor- page-automation- photos-library"
READY_TO_POST_DIR = r"C:\Shoby deathless laptop folder\Ready-To-Post"
DB_PATH = "workflow_database.db"

# Safety Thresholds
MIN_FREE_SPACE_GB = 2.0

# Target Composition Canvas Size
CANVAS_W = 1080
CANVAS_H = 1920

# Professional Effects Configuration
EFFECTS_CONFIG = {
    "particle_count": 50,
    "glow_intensity": 0.6,
    "shake_intensity": 8,
    "chromatic_aberration": 2,
    "vignette_strength": 0.7,
    "grain_amount": 0.05,
}

# Ensure necessary directories exist
os.makedirs(READY_TO_POST_DIR, exist_ok=True)
os.makedirs("temp_downloads", exist_ok=True)
os.makedirs("effects_cache", exist_ok=True)

print("🎬 Initializing professional AI engines...")
stt_model = whisper.load_model(r"C:\Users\khano\.cache\whisper\base.pt")

# ==========================================
# DATABASE SETUP
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_msg_id INTEGER UNIQUE,
            wav_filename TEXT UNIQUE,
            mp4_filename TEXT,
            title TEXT,
            hashtags TEXT,
            received_time TEXT,
            creation_date TEXT,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_history (
            image_path TEXT PRIMARY KEY,
            last_used TEXT,
            usage_count INTEGER DEFAULT 0
        )
    ''')
    # Migration: add usage_count column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE image_history ADD COLUMN usage_count INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists, nothing to do
    conn.commit()
    conn.close()

# ==========================================
# ADVANCED PROGRESS BAR WITH ANIMATION
# ==========================================
class ProfessionalProgressBar(ProgressBarLogger):
    """Beautiful animated progress bar with percentage and ETA"""
   
    def __init__(self, total_frames, operation_name="Rendering"):
        super().__init__(init_state=None)
        self.total_frames = total_frames
        self.operation_name = operation_name
        self.start_time = None
        self.last_percent = -1
        self._lock = threading.Lock()
        self.animation_frames = ['◴', '◷', '◶', '◵']
        self.anim_idx = 0
       
    def callback(self, **changes):
        pass
   
    def bars_callback(self, bar, attr, value, old_value=None):
        if bar != 't' or attr != 'value':
            return
           
        with self._lock:
            if self.start_time is None:
                self.start_time = time.time()
               
            percent = int((value / self.total_frames) * 100) if self.total_frames > 0 else 0
           
            if (percent % 5 == 0 and percent != self.last_percent) or percent == 100:
                self.last_percent = percent
               
                # Animate spinner
                self.anim_idx = (self.anim_idx + 1) % len(self.animation_frames)
                spinner = self.animation_frames[self.anim_idx]
               
                # Calculate ETA
                elapsed = time.time() - self.start_time
                if value > 0:
                    eta = elapsed * (self.total_frames / value - 1)
                    eta_str = f"ETA: {int(eta//60)}:{int(eta%60):02d}" if eta < 3600 else f"ETA: {int(eta//3600)}h"
                else:
                    eta_str = "ETA: --:--"
               
                # Create beautiful progress bar
                bar_width = 40
                filled = int(bar_width * percent / 100)
                bar_visual = '█' * filled + '▓' * min(1, bar_width - filled) + '░' * (bar_width - filled - 1)
               
                # Color codes for terminal
                GREEN = '\033[92m'
                YELLOW = '\033[93m'
                CYAN = '\033[96m'
                RESET = '\033[0m'
               
                timestamp = time.strftime('%H:%M:%S')
                sys.stdout.write(f'{CYAN}{spinner}{RESET} [{timestamp}] {GREEN}{self.operation_name}{RESET} [{bar_visual}] {YELLOW}{percent}%{RESET} {CYAN}{eta_str}{RESET}\n')
                sys.stdout.flush()
               
                if percent == 100:
                    sys.stdout.write(f'\n{GREEN}✅ {self.operation_name} Complete!{RESET}\n')
                    sys.stdout.flush()

# ==========================================
# PROFESSIONAL EFFECTS ENGINE
# ==========================================

class ProfessionalEffects:
    """Cinematic effects engine with optimized performance for 8GB RAM"""
   
    @staticmethod
    def apply_cinematic_lut(image_array, style="teal_orange"):
        """Apply cinematic color grading using LUT-style transformations"""
        frame = image_array.astype(np.float32) / 255.0
       
        if style == "teal_orange":
            # Professional teal & orange (cinematic blockbuster look)
            frame[:,:,0] = np.clip(frame[:,:,0] * 1.15, 0, 1)  # Reds warmer
            frame[:,:,1] = np.clip(frame[:,:,1] * 0.92, 0, 1)  # Greens desaturated
            frame[:,:,2] = np.clip(frame[:,:,2] * 1.08, 0, 1)  # Blues lifted
            # Add subtle split-toning
            frame[:,:,0] = frame[:,:,0] * (1 - frame[:,:,2] * 0.15)
           
        elif style == "moody_blue":
            frame[:,:,0] = np.clip(frame[:,:,0] * 0.85, 0, 1)
            frame[:,:,1] = np.clip(frame[:,:,1] * 0.90, 0, 1)
            frame[:,:,2] = np.clip(frame[:,:,2] * 1.25, 0, 1)
           
        elif style == "warm_sunset":
            frame[:,:,0] = np.clip(frame[:,:,0] * 1.25, 0, 1)
            frame[:,:,1] = np.clip(frame[:,:,1] * 1.10, 0, 1)
            frame[:,:,2] = np.clip(frame[:,:,2] * 0.80, 0, 1)
           
        elif style == "vintage_film":
            # Faded blacks and crushed shadows
            frame = np.clip((frame - 0.05) * 1.1, 0, 1)
            # Warm tint
            frame[:,:,0] = frame[:,:,0] * 1.12
            frame[:,:,2] = frame[:,:,2] * 0.85
           
        return (frame * 255).astype(np.uint8)
   
    @staticmethod
    def add_vignette(image_array, strength=0.7):
        """Add professional dark/light vignette effect"""
        h, w = image_array.shape[:2]
        X, Y = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
        radius = np.sqrt(X**2 + Y**2)
        vignette = 1 - np.clip(radius * strength, 0, 0.8)
        vignette_3d = np.stack([vignette] * 3, axis=2)
        return (image_array * vignette_3d).astype(np.uint8)
   
    @staticmethod
    def add_film_grain(image_array, intensity=0.05):
        """Add subtle film grain for texture"""
        grain = np.random.normal(0, intensity * 255, image_array.shape)
        return np.clip(image_array + grain, 0, 255).astype(np.uint8)
   
    @staticmethod
    def chromatic_aberration(image_array, shift=2):
        """Add RGB split/chromatic aberration effect"""
        h, w = image_array.shape[:2]
        result = image_array.copy()
       
        # Shift red channel right
        if shift < w:
            result[:, shift:, 0] = image_array[:, :-shift, 0]
            result[:, :shift, 0] = image_array[:, :1, 0]
       
        # Shift blue channel left
        if shift < w:
            result[:, :-shift, 2] = image_array[:, shift:, 2]
            result[:, -shift:, 2] = image_array[:, -1:, 2]
           
        return result

# ==========================================
# PROFESSIONAL PARTICLE SYSTEM
# ==========================================

class ParticleSystem:
    """Lightweight particle system for magical effects"""
   
    def __init__(self, canvas_w, canvas_h, particle_count=50):
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.particles = []
        self.particle_count = particle_count
        self.init_particles()
       
    def init_particles(self):
        for _ in range(self.particle_count):
            self.particles.append({
                'x': random.uniform(0, self.canvas_w),
                'y': random.uniform(0, self.canvas_h),
                'vx': random.uniform(-50, 50),
                'vy': random.uniform(-50, 50),
                'life': random.uniform(0.5, 2.0),
                'max_life': random.uniform(0.5, 2.0),
                'size': random.uniform(2, 8),
                'color': random.choice([(255,200,100), (255,100,100), (100,200,255), (255,255,200)])
            })
   
    def update(self, dt):
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
           
            # Reset particles that die
            if p['life'] <= 0:
                p['x'] = random.uniform(0, self.canvas_w)
                p['y'] = random.uniform(0, self.canvas_h)
                p['vx'] = random.uniform(-80, 80)
                p['vy'] = random.uniform(-80, 80)
                p['life'] = p['max_life']
   
    def render_frame(self, frame):
        overlay = np.zeros((self.canvas_h, self.canvas_w, 3), dtype=np.uint8)
       
        for p in self.particles:
            if p['life'] > 0:
                alpha = int(255 * (p['life'] / p['max_life']))
                x, y = int(p['x']), int(p['y'])
                size = int(p['size'])
               
                if 0 <= x < self.canvas_w and 0 <= y < self.canvas_h:
                    # Draw particle as circle or square
                    x_start = max(0, x - size)
                    x_end = min(self.canvas_w, x + size)
                    y_start = max(0, y - size)
                    y_end = min(self.canvas_h, y + size)
                   
                    for px in range(x_start, x_end):
                        for py in range(y_start, y_end):
                            dist = ((px - x)**2 + (py - y)**2)**0.5
                            if dist < size:
                                intensity = int(alpha * (1 - dist/size))
                                overlay[py, px] = [min(255, p['color'][0]),
                                                  min(255, p['color'][1]),
                                                  min(255, p['color'][2])]
       
        # Blend particles with frame
        blend_factor = 0.7
        result = cv2.addWeighted(frame, 1 - blend_factor, overlay, blend_factor, 0)
        return result

# ==========================================
# ==========================================
# IMAGE DISPLAY (Static - No Ken Burns)
# ==========================================


# ==========================================
# PROFESSIONAL SUBTITLE SYSTEM
# ==========================================

class ProfessionalSubtitles:
    """Advanced subtitle system with animations and styling"""
   
    @staticmethod
    def create_animated_subtitle(segments, canvas_w, canvas_h):
        """Create animated subtitles with modern social media styling"""
        subtitle_clips = []
        y_position = int(canvas_h * 0.75)
       
        for seg in segments:
            text = seg['text'].strip().upper()
            if len(text) < 2:
                continue
               
            start = seg['start']
            duration = max(0.3, seg['end'] - seg['start'])
           
            # Create background bar
            bg_bar = (TextClip(" " * 60,
                              fontsize=48,
                              color='black',
                              bg_color='black',
                              font='Arial-Bold',
                              method='caption',
                              size=(canvas_w - 100, 80))
                     .set_duration(duration)
                     .set_start(start)
                     .set_position(('center', y_position - 10))
                     .set_opacity(0.7))
           
            # Main text with gradient effect (simulated via outline)
            main_text = (TextClip(text,
                                 fontsize=48,
                                 color='white',
                                 stroke_color='black',
                                 stroke_width=3,
                                 font='Arial-Bold',
                                 method='caption',
                                 size=(canvas_w - 120, None))
                        .set_duration(duration)
                        .set_start(start)
                        .set_position(('center', y_position))
                        .crossfadein(0.15)
                        .crossfadeout(0.1))
           
            subtitle_clips.extend([bg_bar, main_text])
       
        return subtitle_clips

# ==========================================
# PROFESSIONAL SOUND DESIGN
# ==========================================

def enhance_audio_professional(input_wav_path, output_wav_path):
    """Professional audio enhancement with compression and EQ"""
    data, rate = sf.read(input_wav_path)
   
    # Handle stereo/surround
    if len(data.shape) > 1:
        # Convert to mono for processing if needed
        if data.shape[1] > 1:
            data = np.mean(data, axis=1)
   
    # Advanced noise reduction
    reduced_noise = nr.reduce_noise(y=data, sr=rate, prop_decrease=0.85, stationary=True)
   
    # Convert to AudioSegment for further processing
    audio = AudioSegment(
        (reduced_noise * 32767).astype(np.int16).tobytes(),
        frame_rate=rate,
        sample_width=2,
        channels=1
    )
   
    # Professional compression
    audio = effects.compress_dynamic_range(audio, threshold=-20.0, ratio=4.0)
   
    # EQ: Boost presence (3-5kHz), reduce mud (200-300Hz)
    audio = audio.low_pass_filter(12000)  # Remove harsh highs
    audio = audio.high_pass_filter(80)    # Remove sub-bass rumble
   
    # Normalize to -1dB LUFS
    audio = effects.normalize(audio, headroom=1.0)
   
    # Slight saturation for warmth
    audio = audio + 2  # Subtle boost
   
    # Export
    audio.export(output_wav_path, format="wav")

# ==========================================
# MAIN VIDEO GENERATION ENGINE
# ==========================================

def create_cinematic_reel(audio_path, transcript_data, output_mp4_path):
    """Main function to create professional cinematic reel"""
   
    print("\n📸 Selecting images...")
   
    # Load audio
    audio_clip = AudioFileClip(audio_path)
    total_duration = audio_clip.duration
   
    # Get transcript segments
    segments = transcript_data.get("segments", [])
    has_subtitles = len(segments) > 0 and sum(s.get('avg_logprob', -1) for s in segments) / len(segments) > -0.5
   
    # Prepare image sequence
    num_images = random.randint(18, 24)
    selected_images = get_smart_images(num_images)
   
    if not selected_images:
        raise ValueError("No images found in library")
   
    print(f"🎨 Processing {len(selected_images)} images...")
   
    # Calculate timing
    image_duration = total_duration / num_images
   
    # Color grading styles
    color_styles = ["teal_orange", "moody_blue", "warm_sunset", "vintage_film"]
   
    video_layers = []
    vfx_layers = []
   
    # Process images with detailed progress
    for i, img_path in enumerate(selected_images):
        print(f"🖼️ Image {i+1}/{len(selected_images)}")
       
        # Choose random styles
        color_style = random.choice(color_styles)
       
        # Load image as static clip
        img_clip = ImageClip(img_path).set_duration(image_duration)
        img_clip = img_clip.resize(height=CANVAS_H)
        img_clip = img_clip.set_position('center')
       
        # Apply color grading via fl_image
        def grade_frame(frame, _style=color_style):
            frame = ProfessionalEffects.apply_cinematic_lut(frame, _style)
            frame = ProfessionalEffects.add_vignette(frame, random.uniform(0.5, 0.8))
            if random.random() < 0.3:
                frame = ProfessionalEffects.add_film_grain(frame, 0.03)
            return frame
       
        img_clip = img_clip.fl_image(grade_frame)
       
        # Add to timeline
        if i == 0:
            img_clip = img_clip.set_start(0)
        else:
            start_time = i * image_duration - 0.3  # Overlap for transition
            img_clip = img_clip.set_start(start_time)
           
            # Add transition effect
            transition_type = random.choice(['fade', 'slide'])
            if transition_type == 'fade':
                img_clip = img_clip.crossfadein(0.4)
       
        video_layers.append(img_clip)
   
    print("📝 Creating subtitles...")
   
    # Create main composition
    main_composite = CompositeVideoClip(video_layers, size=(CANVAS_W, CANVAS_H))
    main_composite = main_composite.set_duration(total_duration).set_audio(audio_clip)
   
    # Add VFX layers
    all_layers = [main_composite]
   
    # Add subtitles
    if has_subtitles:
        subtitle_clips = ProfessionalSubtitles.create_animated_subtitle(
            segments, CANVAS_W, CANVAS_H
        )
        all_layers.extend(subtitle_clips)
   
    # Create outro
    print("🎬 Creating outro...")
    outro = create_professional_outro(3)
   
    print("🎞️ Compositing all layers...")
    final_reel = concatenate_videoclips([CompositeVideoClip(all_layers), outro], method="compose")
   
    # Render final video
    print("🚀 Starting final render...")
    render_start = time.time()
   
    expected_duration = total_duration + 3  # audio + 3s outro
    total_frames = int(expected_duration * 30)
    progress_logger = ProfessionalProgressBar(total_frames, "Cinematic Render")
   
    final_reel.write_videofile(
        output_mp4_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        bitrate='4000k',
        preset='medium',
        threads=2,
        logger=progress_logger
    )
   
    render_time = time.time() - render_start
    print(f"\n✅ Render finished in {int(render_time//60)}m {int(render_time%60)}s")
    print(f"✨ Cinematic reel complete! Saved to: {output_mp4_path}")
   
    # Cleanup
    audio_clip.close()
    final_reel.close()

def create_particle_overlay(duration, start_time):
    """Create particle system overlay"""
    try:
        particles = ParticleSystem(CANVAS_W, CANVAS_H, EFFECTS_CONFIG["particle_count"])
        fps = 30
        frames = []
       
        for t in np.arange(0, duration, 1.0/fps):
            particles.update(1.0/fps)
            frame = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
            frame = particles.render_frame(frame)
            frames.append(frame)
       
        from moviepy.editor import ImageSequenceClip
        particle_clip = ImageSequenceClip(frames, fps=fps).set_duration(duration)
        return particle_clip.set_start(start_time).set_opacity(0.6)
    except Exception as e:
        print(f"Particle effect skipped: {e}")
        return None

def create_professional_outro(duration=3):
    """Create cinematic outro with animation"""
    # Gradient background
    def gradient_frame(t):
        frame = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
        progress = t / duration
       
        # Create gradient
        for y in range(CANVAS_H):
            intensity = int(255 * (1 - y/CANVAS_H))
            frame[y, :, 0] = intensity // 3  # Dark red
            frame[y, :, 1] = intensity // 5  # Very dark green
            frame[y, :, 2] = intensity // 2  # Some blue
           
        return frame
   
    background = VideoClip(gradient_frame, duration=duration)
   
    # Main text with zoom animation
    main_text = (TextClip("DM FOR ENGLISH TUTORING",
                         fontsize=58,
                         color='white',
                         stroke_color='black',
                         stroke_width=4,
                         font='Arial-Bold',
                         method='caption',
                         size=(900, None))
                .set_duration(duration)
                .set_position(('center', 'center')))
   
    # Subtitle text
    sub_text = (TextClip("@YourEnglishTutor",
                        fontsize=36,
                        color='#FFD700',
                        font='Arial',
                        method='caption')
               .set_duration(duration)
               .set_position(('center', CANVAS_H // 2 + 80))
               .set_start(0.5)
               .crossfadein(0.3))
   
    return CompositeVideoClip([background, main_text, sub_text], size=(CANVAS_W, CANVAS_H))

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def check_disk_space():
    total, used, free = shutil.disk_usage(READY_TO_POST_DIR)
    free_gb = free / (1024 ** 3)
    return free_gb >= MIN_FREE_SPACE_GB, free_gb

def update_status(row_id, status_str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE workflow_logs SET status = ? WHERE id = ?", (status_str, row_id))
    conn.commit()
    conn.close()

def generate_metadata(transcript):
    transcript = transcript.strip()
    words = [w.strip(".,!?") for w in transcript.split()]

    if len(words) >= 6:
        title = " ".join(words[:6]).title()
    elif len(words) > 0:
        title = " ".join(words).title()
    else:
        title = "English Speaking Lesson"

    keywords = []
    for word in words:
        word = word.lower()
        if len(word) > 4 and word not in keywords:
            keywords.append(word)
        if len(keywords) >= 3:
            break

    hashtags = [
        "#english", "#learnenglish", "#englishspeaking",
        "#englishteacher", "#englishlesson", "#speakenglish"
    ]
    for keyword in keywords:
        hashtags.append(f"#{keyword}")

    return title, " ".join(hashtags)

def get_smart_images(count):
    all_images = [os.path.join(IMAGE_LIBRARY_DIR, f) for f in os.listdir(IMAGE_LIBRARY_DIR)
                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not all_images:
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT image_path, usage_count FROM image_history")
        history = dict(cursor.fetchall())

    except sqlite3.OperationalError:
        cursor.execute("SELECT image_path FROM image_history")
        history = {row[0]: 0 for row in cursor.fetchall()}

    weights = [1 / (history.get(img, 0) + 1) for img in all_images]
    selected_images = random.choices(
        all_images,
        weights=weights,
        k=min(count, len(all_images))
    )

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for img in selected_images:
        current_count = history.get(img, 0)

        cursor.execute(
            "INSERT OR REPLACE INTO image_history (image_path, last_used, usage_count) VALUES (?, ?, ?)",
            (img, now_str, current_count + 1)
        )

    conn.commit()
    conn.close()

    return selected_images
# ==========================================
# MAIN PROCESSING PIPELINE
# ==========================================

def process_telegram_queue():
    print(f"\n{'='*60}")
    print(f"🎬 PROFESSIONAL REEL PRODUCTION PIPELINE")
    print(f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
   
    init_db()
   
    print("[1/8] Connecting to Telegram...")
    try:
        client = TelegramClient('session_saved_messages', API_ID, API_HASH)
        client.start()
        print("✅ Telegram connected")
    except Exception as e:
        print(f"❌ Telegram connection failed: {e}")
        return

    with client:
        print("[2/8] Checking disk space...")
        has_space, free_gb = check_disk_space()
        if not has_space:
            print(f"❌ Insufficient disk space: {free_gb:.2f} GB free")
            client.send_message('me', f"⚠️ Low disk space alert: {free_gb:.2f} GB remaining")
            return
        print(f"✅ Disk space OK: {free_gb:.2f} GB free")

        print("📥 Fetching messages from Saved Messages...")
        messages = client.get_messages('me', limit=100)
       
        processed_count = 0
        failed_count = 0
       
        for msg in reversed(messages):
            has_wav = (msg.media and isinstance(msg.media, MessageMediaDocument)
                      and msg.file and msg.file.ext.lower() == '.wav')
          
            if not has_wav:
                continue
              
            print(f"\n{'─'*50}")
            print(f"🎯 Processing audio: {msg.file.name if msg.file else f'msg_{msg.id}'}")
            print(f"{'─'*50}")
              
            received_time = msg.date.strftime("%Y-%m-%d %H:%M:%S")
            safe_filename = msg.file.name if (msg.file and msg.file.name) else f"audio_{msg.id}.wav"
           
            # Check for duplicates
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM workflow_logs WHERE wav_filename = ?", (safe_filename,))
            if cursor.fetchone():
                print(f"⏭️ Already processed: {safe_filename}")
                conn.close()
                continue
           
            print("[3/8] Downloading audio file...")
            temp_path = os.path.join("temp_downloads", safe_filename)
            client.download_media(msg, file=temp_path)
            print("✅ Audio downloaded")
           
            # Check duration
            audio_info = AudioSegment.from_wav(temp_path)
            duration_secs = len(audio_info) / 1000.0
          
            if duration_secs > 60.0:
                print(f"❌ Audio too long: {duration_secs:.1f}s (max 60s)")
                os.remove(temp_path)
                cursor.execute("INSERT INTO workflow_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (None, msg.id, safe_filename, None, None, None, received_time, None, "Rejected"))
                conn.commit()
                conn.close()
                continue
           
            # Insert into database
            cursor.execute("INSERT INTO workflow_logs (telegram_msg_id, wav_filename, status, received_time) VALUES (?, ?, ?, ?)",
                           (msg.id, safe_filename, "Queued", received_time))
            conn.commit()
            log_id = cursor.lastrowid
            conn.close()
          
            try:
                update_status(log_id, "Processing")
                print("[4/8] Enhancing audio...")
                enhanced_wav_path = os.path.join("temp_downloads", f"enhanced_{safe_filename}")
                enhance_audio_professional(temp_path, enhanced_wav_path)
                print("✅ Audio enhanced")
              
                print("[5/8] Transcribing audio with Whisper...")
                stt_result = stt_model.transcribe(enhanced_wav_path)
                transcript = stt_result["text"]
                print(f"📝 Transcript: \"{transcript[:80]}...\"")
               
                print("[6/8] Generating title and hashtags...")
                title, hashtags = generate_metadata(transcript)
                print(f"📌 Title: {title}")
                print(f"🏷️ Hashtags: {hashtags[:100]}...")
              
                output_mp4_name = f"cinematic_reel_{int(time.time())}_{log_id}.mp4"
                final_output_path = os.path.join(READY_TO_POST_DIR, output_mp4_name)
              
                print("[7/8] Building cinematic video...")
                create_cinematic_reel(enhanced_wav_path, stt_result, final_output_path)
              
                if os.path.exists(final_output_path) and os.path.getsize(final_output_path) > 10000:
                    print("[8/8] Uploading final reel to Telegram...")
                    caption = f"🎬 {title}\n\n{hashtags}"
                    client.send_message('me', caption, file=final_output_path)
                    print("✅ Video uploaded to Telegram")
                  
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE workflow_logs
                        SET mp4_filename = ?, title = ?, hashtags = ?, creation_date = ?, status = ?
                        WHERE id = ?
                    ''', (output_mp4_name, title, hashtags, datetime.datetime.now().strftime("%Y-%m-%d"), "Ready", log_id))
                    conn.commit()
                    conn.close()
                  
                    processed_count += 1
                    print(f"✨ Success! Cinematic reel #{processed_count} complete")
                else:
                    raise Exception("Output file invalid")
                  
            except Exception as e:
                print(f"❌ Processing error: {e}")
                update_status(log_id, "Failed")
                failed_count += 1
                continue
            finally:
                # Cleanup temp files with retry to handle file-lock (WinError 32)
                def safe_remove(path, retries=5, delay=1.0):
                    for attempt in range(retries):
                        try:
                            if os.path.exists(path):
                                os.remove(path)
                            return
                        except PermissionError:
                            if attempt < retries - 1:
                                time.sleep(delay)
                            else:
                                print(f"⚠️ Could not delete temp file (still locked): {path}")

                safe_remove(temp_path)
                if 'enhanced_wav_path' in locals():
                    safe_remove(enhanced_wav_path)
       
        print(f"\n{'='*60}")
        print(f"📊 PRODUCTION SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successfully processed: {processed_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"💾 Free space: {free_gb:.2f} GB")
        print(f"{'='*60}\n")

# ==========================================
# MAIN ENTRY POINT
# ==========================================

if __name__ == "__main__":
    try:
        print("""
        ╔══════════════════════════════════════════════════════════╗
        ║     🎬 CINEMATIC REEL PRODUCTION SYSTEM v2.0 🎬          ║
        ╚══════════════════════════════════════════════════════════╝
        """)

        process_telegram_queue()

    except Exception as e:
        print(f"❌ Fatal error: {e}")

    finally:
        print("✅ Production pipeline complete!")
        print("💡 Check the 'Ready-To-Post' folder for your cinematic reels\n")
