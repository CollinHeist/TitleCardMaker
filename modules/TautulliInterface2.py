from json import dumps
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from modules.Debug import log
from modules.WebInterface import WebInterface

class TautulliInterface(WebInterface):
    """
    This class describes an interface to Tautulli. This interface can
    configure notification agents within Tautulli to enable fast card
    updating/creation.
    """

    """Default configurations for the notification agent(s)"""
    DEFAULT_AGENT_NAME = 'Update TitleCardMaker'

    """Agent ID for a Webhook"""
    AGENT_ID = 25


    def __init__(self,
            tcm_url: str,
            tautulli_url: str,
            api_key: str,
            use_ssl: bool = True,
            agent_name: str = DEFAULT_AGENT_NAME) -> None:
        """
        Construct a new instance of an interface to Sonarr.

        Args:
            tcm_url: Base URL of TitleCardMaker for the API endpoint.
            tautulli_url: The API URL for interfacing with Tautulli.
            api_key: The API key for API requests.
            use_ssl: Whether to use SSL for the interface.
            agent_name: Name of the Notification Agent to check for and/
                or create on Tautulli.

        Raises:
            HTTPException (401) if the URL or API Key is invalid.
            HTTPException (400) if Tautulli cannot be connected to.
        """

        # Initialize parent WebInterface 
        super().__init__('Tautulli', use_ssl, cache=False)

        # Get correct TCM URL
        tcm_url = tcm_url if tcm_url.endswith('/') else f'{tcm_url}/'
        self.tcm_url = f'{tcm_url}api/cards/key'

        # Get correct Tautulli URL
        tautulli_url = tautulli_url if tautulli_url.endswith('/') else f'{tautulli_url}/'
        if tautulli_url.endswith('/api/v2/'):
            self.tautulli_url = tautulli_url
        elif (re_match := self._URL_REGEX.match(tautulli_url)) is None:
            raise HTTPException(
                status_code=422,
                detail=f'Invalid Tautulli URL'
            )
        else:
            self.tautulli_url = f'{re_match.group(1)}/api/v2/'

        # Base parameters for sending requests to Sonarr
        self.__params = {'apikey': api_key}

        # Query system status to verify connection to Tautulli
        try:
            status = self._get(
                self.tautulli_url,
                self.__params | {'cmd': 'status'}
            )
            if status.get('response', {}).get('result') != 'success':
                raise HTTPException(
                    status_code=401,
                    detail=f'Invalid Tautulli URL or API key'
                )
        except Exception as e:
            log.exception(f'Tautulli connection error', e)
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Tautulli',
            )

        # Store attributes
        self.agent_name = agent_name


    def is_integrated(self) -> bool:
        """
        Check if this interface's Tautulli instance already has
        integration set up.

        Returns:
            True if the Notification Agent is already set up.
        """

        # Get all notifiers
        response = self._get(
            self.tautulli_url,
            self.__params | {'cmd': 'get_notifiers'}
        )
        notifiers = response['response']['data']

        # Integrated if any active Webhook agent has this name
        return any(
            (agent['agent_label'] == 'Webhook'
             and agent['friendly_name'] == self.agent_name
             and agent['active'] == 1)
            for agent in notifiers
        )


    def __create_agent(self) -> Optional[int]:
        """
        Create a new Notification Agent.

        Returns:
            Notifier ID of created agent, None if agent was not created.
        """

        # Get all existing notifier ID's
        response = self._get(
            self.tautulli_url,
            self.__params | {'cmd': 'get_notifiers'}
        )['response']['data']
        existing_ids = {agent['id'] for agent in response}

        # Create new notifier
        params = {'cmd': 'add_notifier_config', 'agent_id': self.AGENT_ID}
        self._get(self.tautulli_url,  self.__params | params)

        # Get notifier ID's after adding new one
        response = self._get(
            self.tautulli_url,
            self.__params | {'cmd': 'get_notifiers'}
        )['response']['data']
        new_ids = {agent['id'] for agent in response}

        # If no new ID's are returned
        if len(new_ids - existing_ids) == 0:
            log.error(f'Failed to create new notification agent on Tautulli')
            return None

        # Get ID of created notifier
        return list(new_ids - existing_ids)[0]


    def integrate(self) -> None:
        """
        Integrate this interface's instance of Tautulli with TCM. This
        configures a new notification agent if a valid one does not
        exist or cannot be identified.
        """

        # If already integrated, skip
        if self.is_integrated():
            log.debug('Tautulli integrated detected')
            return None

        # Create Agent, raise if fails
        if (created_id := self.__create_agent()) is None:
            raise HTTPException(
                status_code=400,
                detail='Failed to create Notification Agent',
            )

        # Only condition is that the content be a show, season, or episode
        conditions = [{
            'parameter': 'media_type',
            'operator':  'is',
            'value':     ['show', 'season', 'episode'],
            'type':      'str',
        }]

        # Configure this Agent
        params = self.__params | {
            # API arguments
            'cmd': 'set_notifier_config',
            'notifier_id': created_id,
            'agent_id': self.AGENT_ID,
            # Agent Configuration
            'friendly_name': self.agent_name,
            'webhook_hook': self.tcm_url,
            'webhook_method': 'POST',
            # Agent Triggers
            'on_created': 1,
            'on_watched': 1,
            # Agent Conditions
            'custom_conditions': dumps(conditions),
            # POST Arguments
            'on_created_body': '"{rating_key}"',
            'on_watched_body': '"{rating_key}"',
        }
        self._get(self.tautulli_url, params)
        log.info(f'Created and configured Tautulli notification agent '
                 f'{created_id} ("{self.agent_name}")')