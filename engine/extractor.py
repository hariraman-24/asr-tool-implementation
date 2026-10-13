"""
Lightweight NLP Extractor for VoiceScribe.
Extracts title, concise bullet points summary, and action items from spoken text.
"""

import re

URGENT_WORDS = {"urgent", "critical", "immediately", "asap", "today", "tomorrow", "important"}

def extract_action_items(text):
    """Find clear task statements and action items."""
    sentences = re.split(r"[.?!;\n]+\s*", text)
    items = []

    for s in sentences:
        s_clean = s.strip()
        if not s_clean or len(s_clean) < 8:
            continue

        # Pattern: [Person] will / should / needs to [Task]
        m = re.search(r"([A-Za-z\s]+?)\s+(?:will|should|must|needs\s+to|has\s+to)\s+([^.?!]+)", s_clean, re.IGNORECASE)
        if m:
            assignee = m.group(1).strip().title()
            task_raw = m.group(2).strip()
            # Priority
            priority = "High" if any(w in s_clean.lower() for w in URGENT_WORDS) else "Normal"
            items.append({
                "task": task_raw[0].upper() + task_raw[1:],
                "assignee": assignee,
                "priority": priority,
                "done": False
            })
            continue

        # Pattern: please / need to / remember to [Task]
        m2 = re.search(r"(?:please|need\s+to|remember\s+to|make\s+sure\s+to)\s+([^.?!]+)", s_clean, re.IGNORECASE)
        if m2:
            task_raw = m2.group(1).strip()
            priority = "High" if any(w in s_clean.lower() for w in URGENT_WORDS) else "Normal"
            items.append({
                "task": task_raw[0].upper() + task_raw[1:],
                "assignee": "Me",
                "priority": priority,
                "done": False
            })

    return items

def generate_summary(text):
    """Generate concise bullet points from spoken text."""
    sentences = [s.strip() for s in re.split(r"[.?!]\s+", text) if len(s.strip()) > 10]
    if not sentences:
        return "Spoken notes captured."
    # Return 2-3 most relevant sentences
    return ". ".join(sentences[:3]) + "."

def analyze_speech(text):
    clean_text = re.sub(r"\s+", " ", text).strip()
    words = clean_text.split()
    
    # Generate clean title from first few words
    if len(words) > 5:
        title = " ".join(words[:5]).title() + "..."
    elif words:
        title = " ".join(words).title()
    else:
        title = "Voice Note"

    summary = generate_summary(clean_text)
    action_items = extract_action_items(clean_text)

    return {
        "title": title,
        "summary": summary,
        "action_items": action_items
    }
