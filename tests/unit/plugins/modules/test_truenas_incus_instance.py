# Unit tests for truenas_incus_instance module

import unittest
from unittest.mock import Mock, MagicMock, patch
import json

# Mock the ansible module utils
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../plugins/modules'))

from ansible.module_utils.basic import AnsibleModule


class TestTruenasIncusInstance(unittest.TestCase):
    """Unit tests for truenas_incus_instance module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = Mock(spec=AnsibleModule)
        self.mock_module.params = {
            'name': 'test-container',
            'state': 'present',
            'type': 'CONTAINER',
            'source': {
                'type': 'IMAGE',
                'alias': 'debian/12'
            },
            'config': {
                'limits.cpu': '2',
                'limits.memory': '2GB'
            },
            'devices': {
                'root': {
                    'type': 'disk',
                    'path': '/',
                    'pool': 'default'
                }
            },
            'timeout': 60,
            'api_url': 'https://test.local/api/v2.0',
            'api_key': 'test-key'
        }
        self.mock_module.check_mode = False
        self.mock_module.fail_json = Mock()
        self.mock_module.exit_json = Mock()
    
    def test_get_instance_found(self):
        """Test getting an existing instance"""
        from truenas_incus_instance import get_instance
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': '123', 'name': 'test-container', 'status': 'Running'},
            {'id': '456', 'name': 'other-container', 'status': 'Stopped'}
        ]
        mock_api_client.call.return_value = mock_response
        
        result = get_instance(mock_api_client, 'test-container')
        
        self.assertEqual(result['id'], '123')
        self.assertEqual(result['name'], 'test-container')
        mock_api_client.call.assert_called_once_with('/virt/instance', method='GET')
    
    def test_get_instance_not_found(self):
        """Test getting a non-existent instance"""
        from truenas_incus_instance import get_instance
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': '456', 'name': 'other-container', 'status': 'Stopped'}
        ]
        mock_api_client.call.return_value = mock_response
        
        result = get_instance(mock_api_client, 'non-existent')
        
        self.assertIsNone(result)
    
    def test_get_instance_api_error(self):
        """Test API error when getting instance"""
        from truenas_incus_instance import get_instance
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_api_client.call.return_value = mock_response
        
        result = get_instance(mock_api_client, 'test-container')
        
        self.assertIsNone(result)
    
    def test_create_instance_success(self):
        """Test successful instance creation"""
        from truenas_incus_instance import create_instance
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': '123', 'name': 'test-container'}
        mock_api_client.call.return_value = mock_response
        
        changed, instance = create_instance(self.mock_module, mock_api_client)
        
        self.assertTrue(changed)
        self.assertEqual(instance['id'], '123')
        
        # Verify API call payload
        expected_payload = {
            'name': 'test-container',
            'type': 'CONTAINER',
            'source': {'type': 'IMAGE', 'alias': 'debian/12'},
            'config': {'limits.cpu': '2', 'limits.memory': '2GB'},
            'devices': {'root': {'type': 'disk', 'path': '/', 'pool': 'default'}}
        }
        mock_api_client.call.assert_called_once_with('/virt/instance', method='POST', data=expected_payload)
    
    def test_create_instance_failure(self):
        """Test instance creation failure"""
        from truenas_incus_instance import create_instance
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_api_client.call.return_value = mock_response
        
        create_instance(self.mock_module, mock_api_client)
        
        self.mock_module.fail_json.assert_called_once_with(msg='Failed to create instance: Bad Request')
    
    def test_start_instance_success(self):
        """Test successful instance start"""
        from truenas_incus_instance import start_instance
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_api_client.call.return_value = mock_response
        
        result = start_instance(self.mock_module, mock_api_client, '123')
        
        self.assertTrue(result)
        mock_api_client.call.assert_called_once_with('/virt/instance/123/start', method='POST')
    
    def test_start_instance_already_running(self):
        """Test starting an already running instance"""
        from truenas_incus_instance import start_instance
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 409  # Conflict - already running
        mock_api_client.call.return_value = mock_response
        
        result = start_instance(self.mock_module, mock_api_client, '123')
        
        self.assertTrue(result)
    
    def test_stop_instance_success(self):
        """Test successful instance stop"""
        from truenas_incus_instance import stop_instance
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_api_client.call.return_value = mock_response
        
        result = stop_instance(self.mock_module, mock_api_client, '123')
        
        self.assertTrue(result)
        mock_api_client.call.assert_called_once_with('/virt/instance/123/stop', method='POST')
    
    def test_delete_instance_success(self):
        """Test successful instance deletion"""
        from truenas_incus_instance import delete_instance
        
        mock_api_client = Mock()
        # Mock stop response
        stop_response = Mock()
        stop_response.status_code = 200
        # Mock delete response  
        delete_response = Mock()
        delete_response.status_code = 204
        mock_api_client.call.side_effect = [stop_response, delete_response]
        
        result = delete_instance(self.mock_module, mock_api_client, '123')
        
        self.assertTrue(result)
        
        # Should call stop then delete
        expected_calls = [
            unittest.mock.call('/virt/instance/123/stop', method='POST'),
            unittest.mock.call('/virt/instance/123', method='DELETE')
        ]
        mock_api_client.call.assert_has_calls(expected_calls)
    
    @patch('truenas_incus_instance.time.sleep')
    def test_wait_for_state_success(self, mock_sleep):
        """Test successful state waiting"""
        from truenas_incus_instance import wait_for_state, get_instance
        
        mock_api_client = Mock()
        
        # Mock get_instance to return desired state on second call
        with patch('truenas_incus_instance.get_instance') as mock_get_instance:
            mock_get_instance.side_effect = [
                {'status': 'Starting'},  # First call - not ready
                {'status': 'Running'}    # Second call - ready
            ]
            
            result = wait_for_state(mock_api_client, 'test-container', 'Running', 60)
            
            self.assertTrue(result)
            self.assertEqual(mock_get_instance.call_count, 2)
            mock_sleep.assert_called_once_with(2)
    
    @patch('truenas_incus_instance.time.sleep')
    @patch('truenas_incus_instance.time.time')
    def test_wait_for_state_timeout(self, mock_time, mock_sleep):
        """Test state waiting timeout"""
        from truenas_incus_instance import wait_for_state
        
        # Mock time progression to simulate timeout
        mock_time.side_effect = [0, 30, 65]  # start, middle, timeout
        
        mock_api_client = Mock()
        
        with patch('truenas_incus_instance.get_instance') as mock_get_instance:
            mock_get_instance.return_value = {'status': 'Starting'}  # Never reaches desired state
            
            result = wait_for_state(mock_api_client, 'test-container', 'Running', 60)
            
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()