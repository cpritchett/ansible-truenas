# REST API client for TrueNAS modules that need HTTP API access
# Used by Incus and other modules that don't use middlewared

__metaclass__ = type

import json


class RestApiClient:
    """REST API client for TrueNAS HTTP API endpoints"""
    
    def __init__(self, module, api_url=None, api_key=None):
        self.module = module
        self.api_url = api_url or 'https://localhost/api/v2.0'
        self.api_key = api_key
        
        if not self.api_key:
            self.module.fail_json(msg="api_key is required for REST API access")
            
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def call(self, url, method='GET', data=None, timeout=60):
        """Make HTTP API call using curl (no external dependencies)"""
        
        cmd = ['curl', '-s', '-k', '-X', method]
        
        # Add headers
        for key, value in self.headers.items():
            cmd.extend(['-H', f'{key}: {value}'])
        
        # Add data for POST/PUT requests
        if data and method in ['POST', 'PUT', 'PATCH']:
            if isinstance(data, dict):
                data = json.dumps(data)
            cmd.extend(['-d', data])
        
        # Add timeout
        cmd.extend(['--connect-timeout', str(timeout)])
        
        # Add URL
        if url.startswith('/'):
            url = f"{self.api_url.rstrip('/')}{url}"
        elif not url.startswith('http'):
            url = f"{self.api_url.rstrip('/')}/{url.lstrip('/')}"
        cmd.append(url)
        
        # Execute curl command
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        
        # Create response-like object
        response = ApiResponse(rc, stdout, stderr)
        
        return response


class ApiResponse:
    """Response object to mimic requests.Response interface"""
    
    def __init__(self, rc, stdout, stderr):
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr
        
    @property
    def status_code(self):
        """Return HTTP-like status code based on curl return code"""
        if self.rc == 0:
            return 200  # Success
        elif self.rc == 22:
            # Curl error 22: HTTP error (4xx/5xx)
            # Try to parse actual status from stderr
            if '404' in self.stderr:
                return 404
            elif '401' in self.stderr:
                return 401
            elif '403' in self.stderr:
                return 403
            elif '409' in self.stderr:
                return 409
            elif '500' in self.stderr:
                return 500
            else:
                return 400  # Generic client error
        else:
            return 500  # Server/connection error
    
    def json(self):
        """Parse JSON response"""
        try:
            return json.loads(self.stdout)
        except (json.JSONDecodeError, ValueError):
            return {}
    
    @property
    def text(self):
        """Return response text"""
        return self.stdout if self.stdout else self.stderr