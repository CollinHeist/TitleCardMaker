from json import dumps
from pathlib import Path

from modules.Debug import log
import modules.global_objects as global_objects
from modules.WebInterface import WebInterface

class TautulliInterface(WebInterface):
    """
    This class describes an interface to Tautulli
    """

    DEFAULT_AGENT_NAME = 'Update TitleCardMaker'
    DEFAULT_SCRIPT_TIMEOUT = 60

    """Agent ID for a custom Script"""
    AGENT_ID = 15

    """Only cache one request at a time"""
    CACHE_LENGTH = 1


    def __init__(self, url: str, api_key: str, verify_ssl: bool,
                 update_script: Path, agent_name: str=DEFAULT_AGENT_NAME,
                 script_timeout: int=DEFAULT_SCRIPT_TIMEOUT,
                 username: str=None) -> None:
        """
        Construct a new instance of an interface to Sonarr.

        Args:
            url: The API url communicating with Tautulli.
            api_key: The API key for API requests.
            verify_ssl: Whether to verify SSL requests.

        Raises:
            SystemExit: Invalid Sonarr URL/API key provided.
        """

        # Initialize parent WebInterface 
        super().__init__('Tautulli', verify_ssl)

        # Get correct URL
        url = url if url.endswith('/') else f'{url}/'
        if url.endswith('/api/v2/'):
            self.url = url
        elif (re_match := self._URL_REGEX.match(url)) is None:
            log.critical(f'Invalid Tautulli URL "{url}"')
            exit(1)
        else:
            self.url = f'{re_match.group(1)}/api/v2/'

        # Base parameters for sending requests to Sonarr
        self.__params = {'apikey': api_key}

        # Query system status to verify connection to Tautulli
        try:
            status = self._get(self.url, self.__params | {'cmd': 'status'})
            if status.get('response', {}).get('result') != 'success':
                log.critical(f'Cannot get Tautulli status - invalid URL/API key')
                exit(1)
        except Exception as e:
            log.critical(f'Cannot connect to Tautulli - returned error: "{e}"')
            exit(1)

        # Store attributes
        self.update_script = update_script
        self.agent_name = agent_name
        self.script_timeout = script_timeout
        self.username = username
        

    def is_integrated(self) -> bool:
        """
        Check if this interface's Tautulli instance already has integration set
        up.

        Returns:
            True if Tautulli has integration is already set up, False otherwise.
        """

        # Get all notifiers
        response = self._get(self.url, self.__params | {'cmd': 'get_notifiers'})
        notifiers = response['response']['data']

        # Check each agent's name 
        for agent in notifiers:
            name = agent['friendly_name'].lower()
            if (agent['agent_label'] == 'Script'
                and ('tcm' in name or 'titlecardmaker' in name)):
                log.debug(f'Tautulli already integrated in agent '
                          f'{agent["id"]} ("{agent["friendly_name"]}")')
                return True

        log.debug(f'Tautulli not integrated')
        return False


    def integrate(self) -> None:
        """
        Integrate this interface's instance of Tautulli with TCM. This
        configures a new notification agent if a valid one does not exist or
        cannot be identified.
        """

        # If already integrated, skip
        if self.is_integrated():
            return None
        
        # Get all existing notifier ID's
        response = self._get(self.url, self.__params | {'cmd': 'get_notifiers'})
        existing_ids = {agent['id'] for agent in response['response']['data']}

        # Create new notifier
        params = {'cmd': 'add_notifier_config', 'agent_id': self.AGENT_ID}
        self._get(self.url,  self.__params | params)

        # Get notifier ID's after adding new one
        response = self._get(self.url, self.__params | {'cmd': 'get_notifiers'})
        new_ids = {agent['id'] for agent in response['response']['data']}

        # If no new ID's are returned
        if len(new_ids - existing_ids) == 0:
            log.error(f'Failed to create new notification agent on Tautulli')
            return None
        
        # Get ID of created notifier
        notifier_id = list(new_ids - existing_ids)[0]
        log.info(f'Created Tautulli notification agent {notifier_id}')

        # Determine condition(s)
        # Always add condition for the episode
        conditions = [{
            'parameter': 'media_type', 'operator': 'is', 'value': ['episode'],
        }]
        # Optionally add condition for username (if provided)
        if self.username is not None:
            conditions.append({
                'parameter': 'username',
                'operator':  'is',
                'value':     [self.username],
            })

        # Configure this notifier
        params = self.__params | {
            # API arguments
            'cmd': 'set_notifier_config',
            'notifier_id': notifier_id,
            'agent_id': self.AGENT_ID,
            # Configuration
            'friendly_name': self.agent_name,
            'scripts_script_folder': str(self.update_script.parent.resolve()),
            'scripts_script': str(self.update_script.resolve()),
            'scripts_timeout': self.script_timeout,
            # Triggers
            'on_watched': 1,
            'on_created': 1,
            # Conditions
            'custom_conditions': dumps(conditions),
            # Arguments
            'on_watched_subject': '{rating_key}',
            'on_created_subject': '{rating_key}',
        }
        self._get(self.url, params)
        log.info(f'Configured Tautulli notification agent {notifier_id}')