from faster_whisper import WhisperModel

# Load model once at startup (small = good balance of speed/accuracy for demo)
model = WhisperModel("small", device="cpu", compute_type="int8")

def transcribe_audio(file_path: str) -> str:
    segments, info = model.transcribe(file_path, beam_size=5)
    full_text = " ".join([segment.text for segment in segments])
    return full_text.strip()