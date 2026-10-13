import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_srm_logo(output_path):
    scale = 3
    width, height = 900 * scale, 300 * scale
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_srm = ImageFont.truetype("georgiab.ttf", 68 * scale)
        font_sub = ImageFont.truetype("georgiab.ttf", 16 * scale)
        font_ugc = ImageFont.truetype("georgiai.ttf", 12 * scale)
        font_badge = ImageFont.truetype("georgiab.ttf", 26 * scale)
    except Exception:
        font_srm = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_ugc = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    c_blue = "#164585"
    c_gold = "#d4af37"
    c_dark_gold = "#b8860b"

    cx, cy, r = 110 * scale, 105 * scale, 75 * scale
    
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c_gold)
    draw.ellipse([cx - r + (4*scale), cy - r + (4*scale), cx + r - (4*scale), cy + r - (4*scale)], fill="#ffffff")
    
    r2 = 66 * scale
    draw.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=c_dark_gold)
    draw.ellipse([cx - r2 + (3*scale), cy - r2 + (3*scale), cx + r2 - (3*scale), cy + r2 - (3*scale)], fill=c_blue)
    
    draw.ellipse([cx - 28*scale, cy - 35*scale, cx + 28*scale, cy + 5*scale], fill="#ffffff")
    draw.ellipse([cx - 36*scale, cy - 25*scale, cx + 5*scale, cy + 5*scale], fill="#ffffff")
    draw.ellipse([cx - 5*scale, cy - 25*scale, cx + 36*scale, cy + 5*scale], fill="#ffffff")
    draw.ellipse([cx - 20*scale, cy - 42*scale, cx + 20*scale, cy - 10*scale], fill="#ffffff")
    
    draw.rectangle([cx - 5*scale, cy - 5*scale, cx + 5*scale, cy + 30*scale], fill="#ffffff")
    draw.polygon([(cx - 5*scale, cy + 20*scale), (cx - 15*scale, cy + 35*scale), (cx - 5*scale, cy + 35*scale)], fill="#ffffff")
    draw.polygon([(cx + 5*scale, cy + 20*scale), (cx + 15*scale, cy + 35*scale), (cx + 5*scale, cy + 35*scale)], fill="#ffffff")

    draw.text((220 * scale, 28 * scale), "SRM", fill=c_blue, font=font_srm)
    
    draw.text((395 * scale, 52 * scale), "INSTITUTE OF SCIENCE & TECHNOLOGY", fill=c_blue, font=font_sub)
    draw.text((395 * scale, 74 * scale), "(Deemed to be University u/s 3 of UGC Act, 1956)", fill="#334155", font=font_ugc)
    
    banner_box = [110 * scale, 135 * scale, 760 * scale, 190 * scale]
    draw.rectangle(banner_box, fill=c_blue)
    
    badge_text = "T I R U C H I R A P P A L L I"
    draw.text((225 * scale, 145 * scale), badge_text, fill="#ffffff", font=font_badge)

    final_img = img.resize((900, 300), Image.Resampling.LANCZOS)
    final_img.save(output_path, "PNG")
    print(f"Saved logo matching reference to {output_path}")

def generate_architecture_diagram(output_path):
    width, height = 1200, 480
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arialbd.ttf", 13.5)
        text_font = ImageFont.truetype("arial.ttf", 12.5)
        caption_font = ImageFont.truetype("ariali.ttf", 14)
    except Exception:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        caption_font = ImageFont.load_default()

    boxes = [
        {
            "title": "1. Audio Ingestion",
            "items": ["• Live Microphone", "• Drag-and-Drop Audio", "• Formats: WAV, MP3,", "  WebM, FLAC, M4A"],
            "color": "#0284c7"
        },
        {
            "title": "2. REST API & UI Router",
            "items": ["• FastAPI POST /transcribe", "• Streamlit Dashboard", "• Model Selector (tiny/", "  base/small/medium)"],
            "color": "#0369a1"
        },
        {
            "title": "3. Audio Preprocessor",
            "items": ["• 16 kHz Mono Resample", "• Silero VAD Filter", "• Float32 PCM Tensors", "• Signal Quality Metrics"],
            "color": "#0284c7"
        },
        {
            "title": "4. Faster-Whisper ASR",
            "items": ["• 80-Channel Log-Mel", "• CTranslate2 Transformer", "• CTC / Cross-Attention", "• Fallback Engine"],
            "color": "#0f172a"
        },
        {
            "title": "5. Subtitle Exporter",
            "items": ["• Exporters (.SRT, .VTT)", "• JSON & CSV Payload", "• Real-Time Timestamps", "• Direct Downloads"],
            "color": "#0369a1"
        }
    ]

    box_w = 215
    box_h = 320
    start_x = 20
    gap_x = 22
    top_y = 50

    for i, box in enumerate(boxes):
        x = start_x + i * (box_w + gap_x)
        y = top_y
        
        draw.rectangle([x, y, x + box_w, y + box_h], fill="#f8fafc", outline=box["color"], width=2)
        draw.rectangle([x, y, x + box_w, y + 45], fill=box["color"])
        draw.text((x + 10, y + 14), box["title"], fill="#ffffff", font=title_font)
        
        item_y = y + 60
        for item in box["items"]:
            draw.text((x + 12, item_y), item, fill="#1e293b", font=text_font)
            item_y += 24

        if i < len(boxes) - 1:
            arrow_start_x = x + box_w
            arrow_end_x = arrow_start_x + gap_x
            arrow_y = y + box_h // 2
            draw.line([arrow_start_x, arrow_y, arrow_end_x, arrow_y], fill="#0284c7", width=3)
            draw.polygon([
                (arrow_end_x, arrow_y),
                (arrow_end_x - 7, arrow_y - 5),
                (arrow_end_x - 7, arrow_y + 5)
            ], fill="#0284c7")

    caption = "Fig: End-to-End System Architecture and Audio Pipeline for ASR System"
    draw.text((width // 2 - 240, height - 50), caption, fill="#475569", font=caption_font)

    img.save(output_path, "PNG")
    print(f"Saved architecture diagram to {output_path}")

if __name__ == "__main__":
    out_dir = r"h:\ASR implementation"
    generate_srm_logo(os.path.join(out_dir, "srm_logo.png"))
    generate_architecture_diagram(os.path.join(out_dir, "architecture_diagram.png"))
