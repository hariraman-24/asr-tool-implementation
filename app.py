"""
Streamlit Web User Interface for the Automatic Speech Recognition (ASR) Tool.
"""

import os
import sys
import tempfile
import time
import numpy as np
import streamlit as st

# Configure page layout and design theme
st.set_page_config(
    page_title="ASR Tool - Automatic Speech Recognition",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for premium aesthetics
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e1e2f 0%, #0f172a 100%);
        padding: 1.8rem;
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .main-header h1 {
        color: #38bdf8;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0.4rem;
        margin-bottom: 0;
    }
    .metric-card {
        background: #1e293b;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #334155;
        text-align: center;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
    .stDownloadButton button {
        background-color: #0284c7 !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Add current directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from asr_tool.config import ASRConfig, ModelSize, TaskType, OutputFormat, SUPPORTED_LANGUAGES
from asr_tool.audio_processor import AudioProcessor
from asr_tool.engine import UnifiedASREngine
from asr_tool.exporters import TranscriptExporter


@st.cache_resource
def get_asr_engine():
    """Cache ASR Engine instance for web application."""
    return UnifiedASREngine()


engine = get_asr_engine()

# Header Banner
st.markdown("""
<div class="main-header">
    <h1>🎙️ Automatic Speech Recognition (ASR) Tool</h1>
    <p>High-accuracy multi-lingual speech-to-text transcription, translation, VAD filtering, and subtitle exporter.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.header("⚙️ Model Configuration")

model_choice = st.sidebar.selectbox(
    "Whisper Model Size",
    options=[m.value for m in ModelSize],
    index=1,
    help="Tiny/Base are faster; Small/Medium/Large offer higher transcription accuracy."
)

task_choice = st.sidebar.radio(
    "Task Mode",
    options=["transcribe", "translate"],
    format_func=lambda x: "Transcribe (Speech to Text)" if x == "transcribe" else "Translate (To English)",
    help="Transcribe retains original language text; Translate translates audio into English."
)

language_keys = list(SUPPORTED_LANGUAGES.keys())
language_choice = st.sidebar.selectbox(
    "Source Language",
    options=language_keys,
    format_func=lambda k: f"{SUPPORTED_LANGUAGES[k]} ({k})",
    index=0,
    help="Select 'auto' for automatic language identification."
)

st.sidebar.subheader("Advanced Settings")
device_choice = st.sidebar.selectbox("Device", options=["cpu", "cuda"], index=0)
beam_size = st.sidebar.slider("Beam Search Size", min_value=1, max_value=10, value=5)
vad_filter = st.sidebar.checkbox("Enable Voice Activity Detection (VAD)", value=True)
word_timestamps = st.sidebar.checkbox("Word-level Timestamps", value=True)

config = ASRConfig(
    model_size=ModelSize(model_choice),
    device=device_choice,
    task=TaskType(task_choice),
    language=None if language_choice == "auto" else language_choice,
    beam_size=beam_size,
    vad_filter=vad_filter,
    word_timestamps=word_timestamps
)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎙️ Audio File Transcribe", "⚡ Quick Demo Generator", "📁 Batch Processing", "📖 API & CLI Docs"])

# --- TAB 1: AUDIO TRANSCRIBE & VOICE RECORDER ---
with tab1:
    st.subheader("Select Audio Source")
    input_mode = st.radio("Input Source", options=["📁 File Upload", "🎙️ Live Microphone Recorder"], horizontal=True)

    col_upload, col_preview = st.columns([1, 1])

    uploaded_bytes = None
    base_filename = "transcript_output"
    file_mime = "audio/wav"

    with col_upload:
        if input_mode == "📁 File Upload":
            st.markdown("#### Upload Audio File")
            uploaded_file = st.file_uploader(
                "Choose an audio file",
                type=["wav", "mp3", "flac", "ogg", "m4a", "aac"],
                help="Supported formats: WAV, MP3, FLAC, OGG, M4A"
            )
            if uploaded_file is not None:
                uploaded_bytes = uploaded_file.getvalue()
                base_filename = os.path.splitext(uploaded_file.name)[0]
                file_mime = uploaded_file.type or "audio/wav"
        else:
            st.markdown("#### Live Voice Recorder")
            audio_record = st.audio_input("Click the microphone button to start recording live")
            if audio_record is not None:
                uploaded_bytes = audio_record.getvalue()
                base_filename = "mic_recording"
                file_mime = "audio/wav"

    audio_path_to_process = None

    if uploaded_bytes is not None:
        suffix = ".wav" if input_mode == "🎙️ Live Microphone Recorder" else f"_{base_filename}.wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_bytes)
            audio_path_to_process = tmp_file.name

        with col_preview:
            st.markdown("#### Audio Player & Waveform Metrics")
            st.audio(uploaded_bytes, format=file_mime)
            
            try:
                audio_array, sr = AudioProcessor.load_audio(audio_path_to_process)
                info = AudioProcessor.get_audio_info(audio_array, sr)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Duration", f"{info['duration_seconds']}s")
                m2.metric("Sample Rate", f"{sr} Hz")
                m3.metric("RMS Energy", f"{info['rms_energy']:.4f}")
                m4.metric("Peak Amp", f"{info['peak_amplitude']:.3f}")

                # Display simple waveform preview
                st.line_chart(audio_array[::max(1, int(sr / 200))], height=100)
            except Exception as e:
                st.warning(f"Could not load audio waveform preview: {e}")

        st.markdown("---")
        if st.button("🚀 Start Transcription", type="primary", use_container_width=True):
            with st.spinner(f"Transcribing audio using Whisper '{model_choice}' model..."):
                start_t = time.time()
                try:
                    result = engine.transcribe(audio_path_to_process, config=config)
                    proc_time = time.time() - start_t

                    st.success(f"Transcription Completed in {proc_time:.2f} seconds!")

                    # Results Layout
                    res_col1, res_col2 = st.columns([3, 1])

                    with res_col1:
                        st.subheader("Transcript Output")
                        st.text_area("Full Text", value=result.get("text", ""), height=180)

                    with res_col2:
                        st.subheader("Detection Info")
                        st.write(f"**Language:** {result.get('language', 'Unknown').upper()}")
                        st.write(f"**Confidence:** {result.get('language_probability', 1.0) * 100:.1f}%")
                        st.write(f"**Engine:** {result.get('engine', 'faster-whisper')}")
                        st.write(f"**Duration:** {result.get('duration_seconds', 0)}s")

                    # Segment Timestamps Detail
                    st.subheader("Timed Segments")
                    segments = result.get("segments", [])
                    if segments:
                        segment_data = []
                        for s in segments:
                            segment_data.append({
                                "Segment": f"#{s.get('id', 0)}",
                                "Start (s)": f"{s.get('start', 0.0):.2f}",
                                "End (s)": f"{s.get('end', 0.0):.2f}",
                                "Text": s.get("text", ""),
                                "Confidence": f"{s.get('confidence', 1.0) * 100:.1f}%"
                            })
                        st.dataframe(segment_data, use_container_width=True)

                    # Export Download Buttons
                    st.subheader("📥 Export & Download Subtitles")
                    exp_c1, exp_c2, exp_c3, exp_c4, exp_c5 = st.columns(5)

                    txt_data = TranscriptExporter.to_txt(result)
                    srt_data = TranscriptExporter.to_srt(result)
                    vtt_data = TranscriptExporter.to_vtt(result)
                    json_data = TranscriptExporter.to_json(result)
                    csv_data = TranscriptExporter.to_csv(result)

                    exp_c1.download_button("Download .TXT", data=txt_data, file_name=f"{base_filename}.txt", mime="text/plain")
                    exp_c2.download_button("Download .SRT", data=srt_data, file_name=f"{base_filename}.srt", mime="text/x-subrip")
                    exp_c3.download_button("Download .VTT", data=vtt_data, file_name=f"{base_filename}.vtt", mime="text/vtt")
                    exp_c4.download_button("Download .JSON", data=json_data, file_name=f"{base_filename}.json", mime="application/json")
                    exp_c5.download_button("Download .CSV", data=csv_data, file_name=f"{base_filename}.csv", mime="text/csv")

                except Exception as ex:
                    st.error(f"Transcription Error: {str(ex)}")

        # Cleanup temp audio file
        if audio_path_to_process and os.path.exists(audio_path_to_process):
            try:
                os.remove(audio_path_to_process)
            except Exception:
                pass

# --- TAB 2: QUICK DEMO GENERATOR ---
with tab2:
    st.subheader("Generate Synthetic Test Audio Signal")
    st.info("Don't have an audio file ready? Generate a synthetic audio pulse wave file instantly and run speech recognition benchmark.")

    gen_duration = st.slider("Synthetic Signal Duration (seconds)", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
    
    if st.button("✨ Generate Synthetic Audio & Test Engine", type="primary"):
        with st.spinner("Generating PCM waveform and running ASR pipeline..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix="_demo.wav") as tmp_demo:
                demo_path = tmp_demo.name

            AudioProcessor.create_synthetic_speech_wav(demo_path, duration_sec=gen_duration)
            
            st.audio(demo_path)

            audio_arr, sr = AudioProcessor.load_audio(demo_path)
            info = AudioProcessor.get_audio_info(audio_arr, sr)
            st.json(info)

            res = engine.transcribe(demo_path, config=config)
            st.success("Test Transcription Executed!")
            st.json(res)

            if os.path.exists(demo_path):
                os.remove(demo_path)

# --- TAB 3: BATCH PROCESSING ---
with tab3:
    st.subheader("Batch Audio Transcribe")
    st.markdown("Upload multiple audio files simultaneously to transcribe them all in sequence.")

    batch_files = st.file_uploader(
        "Upload multiple files",
        type=["wav", "mp3", "flac", "ogg", "m4a"],
        accept_multiple_files=True
    )

    if batch_files and st.button("🚀 Process All Batch Files", type="primary"):
        st.write(f"Processing {len(batch_files)} file(s)...")
        progress_bar = st.progress(0)

        results_list = []
        for idx, b_file in enumerate(batch_files):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{b_file.name}") as b_tmp:
                b_tmp.write(b_file.getvalue())
                b_path = b_tmp.name

            try:
                res = engine.transcribe(b_path, config=config)
                results_list.append({"filename": b_file.name, "status": "Success", "text": res.get("text")})
            except Exception as e:
                results_list.append({"filename": b_file.name, "status": "Error", "text": str(e)})

            if os.path.exists(b_path):
                os.remove(b_path)

            progress_bar.progress((idx + 1) / len(batch_files))

        st.success("Batch Processing Finished!")
        st.table(results_list)

# --- TAB 4: API & CLI DOCS ---
with tab4:
    st.subheader("Integration & Documentation Guide")

    st.markdown("### 1. Command Line Interface (CLI)")
    st.code("""
# Transcribe single file
python -m asr_tool.cli transcribe audio.wav --model base --format srt --output-dir ./output

# Transcribe whole folder
python -m asr_tool.cli transcribe ./my_audio_folder/ --model small --format all

# Generate synthetic audio for testing
python -m asr_tool.cli generate-sample demo.wav --duration 4.0

# Inspect audio file specs
python -m asr_tool.cli info sample.wav
    """, language="bash")

    st.markdown("### 2. REST API Microservice")
    st.code("""
# Start FastAPI web server
uvicorn asr_tool.api:app --host 0.0.0.0 --port 8000 --reload

# Call Transcribe Endpoint via cURL
curl -X POST "http://localhost:8000/transcribe?model=base&task=transcribe" \\
  -H "accept: application/json" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@sample.wav"

# Direct Subtitle Export (.srt)
curl -X POST "http://localhost:8000/transcribe/export?format=srt&model=base" \\
  -F "file=@sample.wav" -o subtitle.srt
    """, language="bash")

    st.markdown("### 3. Python API Integration")
    st.code("""
from asr_tool import UnifiedASREngine, ASRConfig, ModelSize, TranscriptExporter

engine = UnifiedASREngine()
config = ASRConfig(model_size=ModelSize.BASE, vad_filter=True)

# Transcribe audio file
result = engine.transcribe("speech.wav", config=config)

print("Text:", result["text"])
print("Language:", result["language"])

# Export Subtitles
srt_content = TranscriptExporter.to_srt(result)
with open("speech.srt", "w", encoding="utf-8") as f:
    f.write(srt_content)
    """, language="python")
