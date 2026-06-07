#!/usr/bin/env python3
import unittest
import json
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, '.')
from alertmanager_ntfy_bridge import app

class TestAlertmanagerBridge(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('alertmanager_ntfy_bridge.requests.post')
    def test_webhook_firing_alert(self, mock_post):
        """Test webhook with firing alert"""
        mock_post.return_value = MagicMock(status_code=200)
        
        payload = {
            "status": "firing",
            "alerts": [{
                "labels": {
                    "alertname": "TestAlert",
                    "severity": "warning"
                },
                "annotations": {
                    "summary": "Test summary",
                    "description": "Test description"
                }
            }]
        }
        
        response = self.app.post('/webhook',
                                data=json.dumps(payload),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), 'OK')
        mock_post.assert_called_once()
        
        call_args = mock_post.call_args
        self.assertIn('Title', call_args[1]['headers'])
        self.assertIn('🔔 TestAlert', call_args[1]['headers']['Title'])

    @patch('alertmanager_ntfy_bridge.requests.post')
    def test_webhook_resolved_alert(self, mock_post):
        """Test webhook with resolved alert"""
        mock_post.return_value = MagicMock(status_code=200)
        
        payload = {
            "status": "resolved",
            "alerts": [{
                "labels": {
                    "alertname": "TestAlert",
                    "severity": "warning"
                },
                "annotations": {
                    "summary": "Test summary",
                    "description": "Test description"
                }
            }]
        }
        
        response = self.app.post('/webhook',
                                data=json.dumps(payload),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        call_args = mock_post.call_args
        self.assertIn('✅ TestAlert Resolved', call_args[1]['headers']['Title'])

    @patch('alertmanager_ntfy_bridge.requests.post')
    def test_webhook_critical_priority(self, mock_post):
        """Test webhook with critical severity sets high priority"""
        mock_post.return_value = MagicMock(status_code=200)
        
        payload = {
            "status": "firing",
            "alerts": [{
                "labels": {
                    "alertname": "CriticalAlert",
                    "severity": "critical"
                },
                "annotations": {
                    "summary": "Critical issue"
                }
            }]
        }
        
        response = self.app.post('/webhook',
                                data=json.dumps(payload),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['headers']['Priority'], '5')

if __name__ == '__main__':
    unittest.main()
