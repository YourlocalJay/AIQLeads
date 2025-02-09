"""
Test suite for template generator end sequence functionality
"""

import unittest
import json
import os
from unittest.mock import patch, mock_open
from datetime import datetime
from aiqleads.core.template_generator import TemplateGenerator

class TestTemplateGeneratorEndSequence(unittest.TestCase):
    def setUp(self):
        self.generator = TemplateGenerator()
        self.test_state = {
            "repo_url": "https://github.com/YourlocalJay/AIQLeads",
            "branch": "main",
            "owner": "YourlocalJay",
            "access": "Full",
            "active_files": [
                "aiqleads/core/template_generator.py",
                "aiqleads/data/project_status.json"
            ]
        }
        
        self.test_status = {
            "last_updated": datetime.now().isoformat(),
            "completed": [
                "Test completed item 1",
                "Test completed item 2"
            ],
            "current_state": {
                "description": "Test current state",
                "active_files": [
                    "aiqleads/core/template_generator.py"
                ]
            },
            "pending": [
                "Test pending task 1",
                "Test pending task 2"
            ]
        }

    def test_should_generate_end_sequence(self):
        """Test end sequence trigger detection"""
        self.assertTrue(self.generator.should_generate_end_sequence("End of chat"))
        self.assertTrue(self.generator.should_generate_end_sequence("end of chat"))
        self.assertFalse(self.generator.should_generate_end_sequence("Not end of chat"))

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"active_components": []}))
    @patch("os.path.exists")
    def test_generate_end_sequence_success(self, mock_exists, mock_file):
        """Test successful end sequence generation"""
        mock_exists.return_value = True
        
        # Mock file operations
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.test_status)
        
        result = self.generator.generate_end_sequence(self.test_state)
        
        # Verify result contains required sections
        self.assertIn("Branch: main", result)
        self.assertIn("Owner: YourlocalJay", result)
        self.assertIn("Files of Interest:", result)
        self.assertIn("Critical Requirements:", result)

    def test_validate_paths(self):
        """Test path validation logic"""
        # Valid paths
        valid_state = {"active_files": ["aiqleads/core/test.py"]}
        self.generator._validate_paths(valid_state)  # Should not raise exception
        
        # Invalid paths
        invalid_state = {"active_files": ["invalid/path/test.py"]}
        with self.assertRaises(ValueError):
            self.generator._validate_paths(invalid_state)

    @patch("os.path.exists")
    def test_mvp_mode_path_validation(self, mock_exists):
        """Test MVP mode path validation"""
        mock_exists.return_value = True
        self.generator.set_mvp_mode(True)
        
        # Valid MVP paths
        self.assertTrue(self.generator.validate_mvp_path("backend/test.py"))
        self.assertTrue(self.generator.validate_mvp_path("ai_models/test.py"))
        
        # Invalid MVP paths
        self.assertFalse(self.generator.validate_mvp_path("invalid/path/test.py"))

    def test_format_repository_section(self):
        """Test repository section formatting"""
        result = self.generator._format_repository_section(self.test_state)
        self.assertIn("Branch: main", result)
        self.assertIn("Owner: YourlocalJay", result)
        self.assertIn("Access: Full", result)

    @patch("builtins.open", new_callable=mock_open)
    def test_update_project_status(self, mock_file):
        """Test project status update logic"""
        self.generator._update_project_status(self.test_status, self.test_state)
        
        # Verify file was written
        mock_file.assert_called()
        
        # Verify status was updated
        handle = mock_file()
        handle.write.assert_called_once()
        written_data = handle.write.call_args[0][0]
        self.assertIn("last_updated", written_data)
        self.assertIn("active_files", written_data)

if __name__ == "__main__":
    unittest.main()