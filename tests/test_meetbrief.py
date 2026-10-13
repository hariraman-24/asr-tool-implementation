"""
Automated Test Suite for MeetBrief.
Tests speech recognition fallback, NLP extraction, SQLite database integrity,
action item tracking, and PDF Minutes of Meeting report generation.
"""

import os
import unittest
import tempfile
import json
from datetime import datetime

from database.db import (
    init_db, save_meeting, get_all_meetings, get_meeting_by_id,
    delete_meeting, get_all_action_items, update_action_item_status,
    add_action_item, delete_action_item, get_dashboard_stats
)
from engine.extractor import (
    analyze_meeting, extract_action_items, extract_decisions,
    extract_attendees, extract_title, generate_summary, determine_priority
)
from engine.speech_recognizer import SpeechRecognizer
from engine.pdf_generator import generate_mom_pdf


class TestMeetBrief(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_nlp_title_extraction(self):
        """Test intelligent title identification."""
        text = "Welcome to our B.Tech Capstone Project Technical Review with Dr. Baskar."
        title = extract_title(text)
        self.assertIn("Capstone", title)

    def test_02_nlp_attendee_extraction(self):
        """Test detection of participants and faculty members."""
        text = "In attendance today were Dr. R. Baskar, Rahul, and Priya."
        attendees = extract_attendees(text)
        self.assertTrue(any("Dr. R. Baskar" in a or "Baskar" in a for a in attendees))
        self.assertTrue(any("Rahul" in a for a in attendees))
        self.assertTrue(any("Priya" in a for a in attendees))

    def test_03_nlp_decision_extraction(self):
        """Test extraction of formalized decisions."""
        text = (
            "We discussed the inference engine. "
            "We decided to use CTranslate2 int8 quantization for CPU deployment. "
            "Also agreed to schedule the final viva demo next Thursday."
        )
        decisions = extract_decisions(text)
        self.assertGreaterEqual(len(decisions), 2)
        self.assertTrue(any("quantization" in d.lower() for d in decisions))

    def test_04_nlp_action_items_extraction(self):
        """Test structured action item extraction (Task, Assignee, Due Date, Priority)."""
        text = (
            "Rahul will optimize speech latency by Friday. "
            "Karthik needs to test the SQLite cascading deletes before Monday. "
            "Priya, please urgently build the waveform visualizer today."
        )
        items = extract_action_items(text)
        self.assertGreaterEqual(len(items), 3)

        # Check first task
        r_task = next((it for it in items if "Rahul" in it["assignee"]), None)
        self.assertIsNotNone(r_task)
        self.assertIn("optimize", r_task["task"].lower())
        self.assertIn("Friday", r_task["due_date"])

        # Check urgent priority
        p_task = next((it for it in items if "Priya" in it["assignee"]), None)
        self.assertIsNotNone(p_task)
        self.assertEqual(p_task["priority"], "High")

    def test_05_database_meeting_and_action_item_lifecycle(self):
        """Test saving meeting, action items, and database integrity."""
        title = "Automated Test Session"
        transcript = "Rahul will complete documentation by Friday. We decided to approve the PR."
        analysis = analyze_meeting(transcript)

        meeting_id = save_meeting(
            title=title,
            date="2026-10-13",
            time_str="11:00 AM",
            department="Computer Science & Engineering",
            duration_seconds=180,
            raw_transcript=transcript,
            summary=analysis["summary"],
            attendees=analysis["attendees"],
            decisions=analysis["decisions"],
            action_items=analysis["action_items"]
        )
        self.assertIsInstance(meeting_id, int)

        # Retrieve meeting
        m = get_meeting_by_id(meeting_id)
        self.assertIsNotNone(m)
        self.assertEqual(m["title"], title)
        self.assertGreaterEqual(len(m["action_items"]), 1)

        # Toggle action item status
        item = m["action_items"][0]
        self.assertEqual(item["status"], "Pending")

        update_action_item_status(item["id"], "Completed")
        m_updated = get_meeting_by_id(meeting_id)
        self.assertEqual(m_updated["action_items"][0]["status"], "Completed")
        self.assertIsNotNone(m_updated["action_items"][0]["completed_at"])

        # Add manual action item
        new_item_id = add_action_item(meeting_id, "Prepare testing report", "Priya", "Tomorrow", "High")
        self.assertIsInstance(new_item_id, int)

        # Delete manual item
        del_success = delete_action_item(new_item_id)
        self.assertTrue(del_success)

        # Delete meeting and verify cascading deletion
        m_del = delete_meeting(meeting_id)
        self.assertTrue(m_del)
        self.assertIsNone(get_meeting_by_id(meeting_id))

    def test_06_dashboard_stats_calculation(self):
        """Test KPI metric calculations."""
        stats = get_dashboard_stats()
        self.assertIn("total_meetings", stats)
        self.assertIn("total_tasks", stats)
        self.assertIn("completed_tasks", stats)
        self.assertIn("completion_rate", stats)
        self.assertIn("priority_counts", stats)
        self.assertIsInstance(stats["completion_rate"], (int, float))

    def test_07_speech_recognizer_silence_handling(self):
        """Test silence detection on empty or silent audio."""
        recognizer = SpeechRecognizer.get_instance()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(b"")  # Empty file
            tmp_path = tmp.name

        try:
            res = recognizer.transcribe(tmp_path)
            self.assertEqual(res["text"], "")
            self.assertIn("error", res)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_08_pdf_mom_generation(self):
        """Test generation of official Minutes of Meeting PDF."""
        sample_meeting = {
            "id": 999,
            "title": "B.Tech Final Technical Review",
            "date": "2026-10-13",
            "time": "02:30 PM",
            "department": "Computer Science & Engineering",
            "duration_seconds": 360,
            "summary": "Comprehensive architecture review with Dr. Baskar and student leads.",
            "attendees": ["Dr. R. Baskar", "Rahul", "Priya", "Karthik"],
            "decisions": ["Approve deployment on department server", "Conduct student user trials"],
            "action_items": [
                {"task": "Deploy Docker container to server", "assignee": "Rahul", "priority": "High", "due_date": "Friday", "status": "Pending"},
                {"task": "Prepare user manual documentation", "assignee": "Priya", "priority": "Medium", "due_date": "Monday", "status": "Completed"}
            ],
            "raw_transcript": "Team discussed the server deployment and documentation."
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name

        try:
            success = generate_mom_pdf(sample_meeting, pdf_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 500)  # Valid PDF size
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)


if __name__ == "__main__":
    unittest.main()
