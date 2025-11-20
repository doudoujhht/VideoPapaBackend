import os
import subprocess
import uuid
from flask import Flask, request, send_file, after_this_request
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Enable CORS to allow your frontend to talk to this backend
CORS(app)

UPLOAD_FOLDER = '/tmp' if os.path.exists('/tmp') else './temp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/convert', methods=['POST'])
def convert():
    # 1. Validation
    if 'audio' not in request.files or 'image' not in request.files:
        return {"error": "Missing audio or image file"}, 400

    audio = request.files['audio']
    image = request.files['image']
    
    # 2. Setup unique filenames to prevent collisions
    session_id = str(uuid.uuid4())
    audio_filename = secure_filename(f"{session_id}_{audio.filename}")
    image_filename = secure_filename(f"{session_id}_{image.filename}")
    output_filename = f"{session_id}_output.mp4"

    audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)
    image_path = os.path.join(UPLOAD_FOLDER, image_filename)
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)

    try:
        # 3. Save Uploads
        audio.save(audio_path)
        image.save(image_path)

        # 4. Run FFmpeg via Subprocess
        # This runs the actual conversion command on the server's OS
        command = [
            'ffmpeg',
            '-loop', '1',              # Loop the image
            '-i', image_path,          # Input Image
            '-i', audio_path,          # Input Audio
            '-c:v', 'libx264',         # Video Codec
            '-tune', 'stillimage',     # Tuning for static image
            '-c:a', 'aac',             # Audio Codec
            '-b:a', '192k',            # Audio Bitrate
            '-pix_fmt', 'yuv420p',     # Pixel format for compatibility
            '-shortest',               # End video when audio ends
            '-y',                      # Overwrite output if exists
            output_path
        ]

        # Run command and capture output
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            print("FFmpeg Error:", result.stderr.decode('utf-8'))
            return {"error": "Conversion failed on server"}, 500

        # 5. Return the file and cleanup
        @after_this_request
        def remove_files(response):
            try:
                if os.path.exists(audio_path): os.remove(audio_path)
                if os.path.exists(image_path): os.remove(image_path)
                if os.path.exists(output_path): os.remove(output_path)
            except Exception as e:
                print(f"Error removing files: {e}")
            return response

        return send_file(output_path, mimetype='video/mp4', as_attachment=True, download_name='converted.mp4')

    except Exception as e:
        print(f"Server Error: {e}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    # Run on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)