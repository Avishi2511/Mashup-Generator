from flask import Flask, request, render_template
import os
import subprocess
import yt_dlp
import moviepy.editor as mp
from pydub import AudioSegment
from validate_email_address import validate_email

app = Flask(__name__)

def create_directories(directories):
    for folder in directories:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created directory: {folder}")

def download_videos(singer_name, n_videos, video_folder):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  
        'outtmpl': f'{video_folder}/%(title)s.%(ext)s',  
        'noplaylist': True, 
        'ignoreerrors': True, 
    }
    
    search_query = f"ytsearch{n_videos}:{singer_name}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([search_query]) 
            print(f"Downloaded {n_videos} videos of {singer_name}.")
        except Exception as e:
            print(f"Failed to download videos: {e}")


def extract_audio_from_videos(video_folder, audio_folder):
    video_files = [f for f in os.listdir(video_folder) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))]

    if video_files:
        print(f"Found {len(video_files)} video files in the '{video_folder}' folder.")

        for video_file in video_files:
            video_path = os.path.join(video_folder, video_file)
            audio_file_name = os.path.splitext(video_file)[0] + ".mp3"
            audio_path = os.path.join(audio_folder, audio_file_name)

            try:
                video = mp.VideoFileClip(video_path)
                audio = video.audio
                if audio:  
                    audio.write_audiofile(audio_path)
                    print(f"Extracted audio from {video_file} successfully!")
                else:
                    print(f"No audio stream found in {video_file}")
            except Exception as e:
                print(f"Failed to extract audio from {video_file}: {e}")
    else:
        print(f"No video files found in the '{video_folder}' folder.")

def trim_audio_files(audio_folder, trimmed_audio_folder, trim_duration_ms):
    for filename in os.listdir(audio_folder):
        if filename.endswith('.mp3'): 
            audio = AudioSegment.from_file(os.path.join(audio_folder, filename))
            trimmed_audio = audio[:trim_duration_ms] 

            output_trim_path = os.path.join(trimmed_audio_folder, filename)
            trimmed_audio.export(output_trim_path, format="wav")  

            print(f"Trimmed {filename} and saved to {output_trim_path}")

def merge_trimmed_audio(trimmed_audio_folder, output_file):
    merged_audio = AudioSegment.empty()

    for filename in sorted(os.listdir(trimmed_audio_folder)):
        if filename.endswith('.wav') or filename.endswith('.mp3'):  
            file_path = os.path.join(trimmed_audio_folder, filename)
            print(f"Adding {file_path} to the merged audio")

            audio = AudioSegment.from_file(file_path)
            merged_audio += audio

    merged_audio.export(output_file, format="wav")
    print(f"Merged audio saved as {output_file}")

def create_singer_audio_mashup(singer_name, n_videos, trim_duration, output_file):
    video_folder = "videos"
    audio_folder = "audio"
    trimmed_audio_folder = "trimmed_audios"

    trim_duration_ms = trim_duration * 1000

    create_directories([video_folder, audio_folder, trimmed_audio_folder])

    download_videos(singer_name, n_videos, video_folder)

    extract_audio_from_videos(video_folder, audio_folder)

    trim_audio_files(audio_folder, trimmed_audio_folder, trim_duration_ms)

    merge_trimmed_audio(trimmed_audio_folder, output_file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-mashup', methods=['POST'])
def create_mashup():
    singer_name = request.form['singer_name']
    n_videos = int(request.form['n_videos'])
    duration = int(request.form['duration'])
    output_file = request.form['output_file']
    email = request.form['email']

    if n_videos < 10:
        return "Number of videos must be at least 10.", 400
    if duration < 20:
        return "Duration must be at least 20 seconds.", 400
    if not validate_email(email):
        return "Invalid email address.", 400

    try:
        create_singer_audio_mashup(singer_name, n_videos, duration, output_file)
        return f"Mashup created and sent to {email}!"
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
