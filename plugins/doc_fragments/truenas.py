# Documentation fragment for TrueNAS API connection parameters

__metaclass__ = type


class ModuleDocFragment(object):

    # Standard TrueNAS connection documentation fragment
    DOCUMENTATION = r'''
options:
    api_url:
        description:
            - URL of the TrueNAS API endpoint
            - Should include protocol and port if non-standard
        type: str
        required: false
        default: https://localhost/api/v2.0
    api_key:
        description:
            - API key for authentication with TrueNAS
            - Can be generated in the TrueNAS web interface under System > API Keys
            - Required for API-based modules
        type: str
        required: false

notes:
    - This module requires TrueNAS SCALE 25.04 (Fangtooth) or later for Incus support
    - API key authentication is required - username/password auth is not supported
    - Ensure your API key has sufficient privileges for the operations you want to perform
    - For security, store API keys in Ansible Vault or environment variables
    - The TrueNAS host certificate is not verified (uses -k/--insecure with curl)
'''