# Unit tests for truenas_incus_exec module

import unittest
from unittest.mock import Mock, MagicMock, patch
import json

# Mock the ansible module utils
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../plugins/modules'))

from ansible.module_utils.basic import AnsibleModule


class TestTruenasIncusExec(unittest.TestCase):
    """Unit tests for truenas_incus_exec module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = Mock(spec=AnsibleModule)
        self.mock_module.params = {
            'name': 'test-container',
            'command': 'echo hello world',
            'timeout': 300,
            'api_url': 'https://test.local/api/v2.0',
            'api_key': 'test-key'
        }
        self.mock_module.check_mode = False
        self.mock_module.fail_json = Mock()
        self.mock_module.exit_json = Mock()
    
    def test_get_instance_id_found(self):
        """Test getting instance ID for existing instance"""
        from truenas_incus_exec import get_instance_id
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': '123', 'name': 'test-container'},
            {'id': '456', 'name': 'other-container'}
        ]
        mock_api_client.call.return_value = mock_response
        
        result = get_instance_id(mock_api_client, 'test-container')
        
        self.assertEqual(result, '123')
        mock_api_client.call.assert_called_once_with('/virt/instance', method='GET')
    
    def test_get_instance_id_not_found(self):
        """Test getting instance ID for non-existent instance"""
        from truenas_incus_exec import get_instance_id
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': '456', 'name': 'other-container'}
        ]
        mock_api_client.call.return_value = mock_response
        
        result = get_instance_id(mock_api_client, 'non-existent')
        
        self.assertIsNone(result)
    
    def test_get_instance_id_api_error(self):
        """Test API error when getting instance ID"""
        from truenas_incus_exec import get_instance_id
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_api_client.call.return_value = mock_response
        
        result = get_instance_id(mock_api_client, 'test-container')
        
        self.assertIsNone(result)
    
    def test_execute_command_string_success(self):
        """Test successful command execution with string command"""
        from truenas_incus_exec import execute_command
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'stdout': 'hello world\n',
            'stderr': '',
            'return': 0
        }
        mock_api_client.call.return_value = mock_response
        
        result = execute_command(mock_api_client, '123', 'echo hello world')
        
        self.assertEqual(result['stdout'], 'hello world\n')
        self.assertEqual(result['stderr'], '')
        self.assertEqual(result['rc'], 0)
        
        # Verify API call
        expected_payload = {
            'command': ['/bin/sh', '-c', 'echo hello world'],
            'wait_for_websocket': False,
            'interactive': False,
            'timeout': 300
        }
        mock_api_client.call.assert_called_once_with('/virt/instance/123/exec', method='POST', data=expected_payload, timeout=310)
    
    def test_execute_command_list_success(self):
        """Test successful command execution with list command"""
        from truenas_incus_exec import execute_command
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'stdout': 'hello world\n',
            'stderr': '',
            'return': 0
        }
        mock_api_client.call.return_value = mock_response
        
        result = execute_command(mock_api_client, '123', ['echo', 'hello', 'world'])
        
        self.assertEqual(result['rc'], 0)
        
        # Verify API call with list command
        expected_payload = {
            'command': ['echo', 'hello', 'world'],
            'wait_for_websocket': False,
            'interactive': False,
            'timeout': 300
        }
        mock_api_client.call.assert_called_once_with('/virt/instance/123/exec', method='POST', data=expected_payload, timeout=310)
    
    def test_execute_command_with_chdir(self):
        """Test command execution with chdir"""
        from truenas_incus_exec import execute_command
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'stdout': '', 'stderr': '', 'return': 0}
        mock_api_client.call.return_value = mock_response
        
        execute_command(mock_api_client, '123', 'ls -la', chdir='/tmp')
        
        # Should wrap command with cd
        expected_payload = {
            'command': ['/bin/sh', '-c', "cd '/tmp' && ls -la"],
            'wait_for_websocket': False,
            'interactive': False,
            'timeout': 300
        }
        mock_api_client.call.assert_called_once_with('/virt/instance/123/exec', method='POST', data=expected_payload, timeout=310)
    
    def test_execute_command_with_environment(self):
        """Test command execution with environment variables"""
        from truenas_incus_exec import execute_command
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'stdout': '', 'stderr': '', 'return': 0}
        mock_api_client.call.return_value = mock_response
        
        env = {'PATH': '/usr/bin:/bin', 'USER': 'testuser'}
        execute_command(mock_api_client, '123', 'env', environment=env)
        
        expected_payload = {
            'command': ['/bin/sh', '-c', 'env'],
            'wait_for_websocket': False,
            'interactive': False,
            'timeout': 300,
            'environment': env
        }
        mock_api_client.call.assert_called_once_with('/virt/instance/123/exec', method='POST', data=expected_payload, timeout=310)
    
    def test_execute_command_failure(self):
        """Test command execution failure"""
        from truenas_incus_exec import execute_command
        
        mock_api_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_api_client.call.return_value = mock_response
        
        result = execute_command(mock_api_client, '123', 'echo hello')
        
        self.assertEqual(result['rc'], 1)
        self.assertEqual(result['stdout'], '')
        self.assertIn('Internal Server Error', result['stderr'])
    
    def test_check_path_exists_true(self):
        """Test path exists check when path exists"""
        from truenas_incus_exec import check_path_exists
        
        mock_api_client = Mock()
        
        with patch('truenas_incus_exec.execute_command') as mock_exec:
            mock_exec.return_value = {'rc': 0}
            
            result = check_path_exists(mock_api_client, '123', '/etc/passwd')
            
            self.assertTrue(result)
            mock_exec.assert_called_once_with(mock_api_client, '123', "test -e '/etc/passwd'", timeout=10)
    
    def test_check_path_exists_false(self):
        """Test path exists check when path doesn't exist"""
        from truenas_incus_exec import check_path_exists
        
        mock_api_client = Mock()
        
        with patch('truenas_incus_exec.execute_command') as mock_exec:
            mock_exec.return_value = {'rc': 1}
            
            result = check_path_exists(mock_api_client, '123', '/nonexistent/file')
            
            self.assertFalse(result)
    
    def test_main_creates_condition_skip(self):
        """Test main function with creates condition that causes skip"""
        from truenas_incus_exec import main
        
        self.mock_module.params['creates'] = '/usr/local/bin/matchbox'
        
        with patch('truenas_incus_exec.RestApiClient') as mock_client_class:
            with patch('truenas_incus_exec.get_instance_id') as mock_get_id:
                with patch('truenas_incus_exec.check_path_exists') as mock_check:
                    mock_get_id.return_value = '123'
                    mock_check.return_value = True  # Path exists, should skip
                    
                    main()
                    
                    self.mock_module.exit_json.assert_called_once()
                    call_args = self.mock_module.exit_json.call_args[1]
                    self.assertFalse(call_args['changed'])
                    self.assertIn('already exists', call_args['msg'])
    
    def test_main_removes_condition_skip(self):
        """Test main function with removes condition that causes skip"""
        from truenas_incus_exec import main
        
        self.mock_module.params['removes'] = '/tmp/lockfile'
        
        with patch('truenas_incus_exec.RestApiClient') as mock_client_class:
            with patch('truenas_incus_exec.get_instance_id') as mock_get_id:
                with patch('truenas_incus_exec.check_path_exists') as mock_check:
                    mock_get_id.return_value = '123'
                    mock_check.return_value = False  # Path doesn't exist, should skip
                    
                    main()
                    
                    self.mock_module.exit_json.assert_called_once()
                    call_args = self.mock_module.exit_json.call_args[1]
                    self.assertFalse(call_args['changed'])
                    self.assertIn('does not exist', call_args['msg'])
    
    def test_main_instance_not_found(self):
        """Test main function when instance is not found"""
        from truenas_incus_exec import main
        
        with patch('truenas_incus_exec.RestApiClient') as mock_client_class:
            with patch('truenas_incus_exec.get_instance_id') as mock_get_id:
                mock_get_id.return_value = None  # Instance not found
                
                main()
                
                self.mock_module.fail_json.assert_called_once_with(msg="Instance 'test-container' not found")
    
    def test_main_check_mode(self):
        """Test main function in check mode"""
        from truenas_incus_exec import main
        
        self.mock_module.check_mode = True
        
        with patch('truenas_incus_exec.RestApiClient') as mock_client_class:
            with patch('truenas_incus_exec.get_instance_id') as mock_get_id:
                mock_get_id.return_value = '123'
                
                main()
                
                self.mock_module.exit_json.assert_called_once()
                call_args = self.mock_module.exit_json.call_args[1]
                self.assertTrue(call_args['changed'])
                self.assertIn('check mode', call_args['msg'])


if __name__ == '__main__':
    unittest.main()