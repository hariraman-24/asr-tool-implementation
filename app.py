"""
MeetBrief: Live Meeting Platform with Real-Time ASR & Minutes of Meeting (MoM).
"""

import os
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

from database.db import (
    init_db,
    save_meeting_mom,
    get_all_meetings,
    get_meeting_by_id,
    delete_meeting
)
from engine.speech_recognizer import SpeechRecognizer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'meetbrief-platform-2026'

init_db()

@app.route('/')
def index():
    meetings = get_all_meetings(limit=10)
    return render_template('index.html', meetings=meetings)

@app.route('/api/save-mom', methods=['POST'])
def api_save_mom():
    title = request.form.get('title', 'General Team Discussion').strip() or 'General Team Discussion'
    mom_text = request.form.get('mom_text', '').strip()
    duration = request.form.get('duration', '00:00').strip()

    if not mom_text:
        return jsonify({"success": False, "error": "No Minutes of Meeting text to save."}), 400

    meeting_id = save_meeting_mom(title=title, mom_text=mom_text, duration=duration)
    return jsonify({
        "success": True,
        "meeting_id": meeting_id,
        "title": title,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%I:%M %p"),
        "duration": duration
    })

@app.route('/api/meetings')
def api_get_meetings():
    meetings = get_all_meetings()
    return jsonify({"success": True, "meetings": meetings})

@app.route('/api/meeting/<int:meeting_id>', methods=['DELETE'])
def api_delete_meeting(meeting_id):
    deleted = delete_meeting(meeting_id)
    return jsonify({"success": deleted})

@app.route('/api/meeting/<int:meeting_id>/download')
def api_download_meeting(meeting_id):
    m = get_meeting_by_id(meeting_id)
    if not m:
        return "Meeting not found", 404

    content = f"MINUTES OF THE MEETING (MoM)\n"
    content += f"Subject: {m['title']}\n"
    content += f"Date: {m['date']} | Time: {m['time']} | Duration: {m['duration']}\n"
    content += "=" * 60 + "\n\n"
    content += m['mom_text'] + "\n"

    safe_title = "".join(c for c in m['title'] if c.isalnum() or c in (' ', '_', '-')).strip()
    filename = f"MoM_{safe_title}_{m['date']}.txt"

    return send_file(
        io.BytesIO(content.encode('utf-8')),
        as_attachment=True,
        download_name=filename,
        mimetype="text/plain"
    )

@app.route('/api/transcribe-audio', methods=['POST'])
def api_transcribe_audio():
    """ASR endpoint for recorded audio files using Faster-Whisper."""
    if 'audio' not in request.files or not request.files['audio'].filename:
        return jsonify({"success": False, "error": "No audio file provided."}), 400

    audio_file = request.files['audio']
    audio_bytes = audio_file.read()
    if len(audio_bytes) == 0:
        return jsonify({"success": False, "error": "Empty audio file."}), 400

    recognizer = SpeechRecognizer.get_instance()
    res = recognizer.transcribe_bytes(audio_bytes)

    if not res.get("text"):
        return jsonify({"success": False, "error": res.get("error", "Could not transcribe audio.")}), 400

    return jsonify({
        "success": True,
        "transcript": res["text"],
        "engine": res.get("engine", "Faster-Whisper ASR")
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"MeetBrief Platform running at http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
