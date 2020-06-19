# -*- coding: utf-8 -*-
"""Webex Teams API wrappers.

Copyright (c) 2016-2019 Cisco and/or its affiliates.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from webexteamssdk.config import (
    DEFAULT_BASE_URL,
    DEFAULT_SINGLE_REQUEST_TIMEOUT,
    DEFAULT_WAIT_ON_RATE_LIMIT,
)
from webexteamssdk.environment import WEBEX_TEAMS_ACCESS_TOKEN
from webexteamssdk.exceptions import AccessTokenError
from webexteamssdk.models.immutable import immutable_data_factory

from webexteamssdk.aio.restsession import AsyncRestSession
from webexteamssdk.aio.api.access_tokens import AsyncAccessTokensAPI
from webexteamssdk.aio.api.attachment_actions import AsyncAttachmentActionsAPI
from webexteamssdk.aio.api.events import AsyncEventsAPI
from webexteamssdk.aio.api.guest_issuer import AsyncGuestIssuerAPI
from webexteamssdk.aio.api.licenses import AsyncLicensesAPI
from webexteamssdk.aio.api.memberships import AsyncMembershipsAPI
from webexteamssdk.aio.api.messages import AsyncMessagesAPI
from webexteamssdk.aio.api.organizations import AsyncOrganizationsAPI
from webexteamssdk.aio.api.people import AsyncPeopleAPI
from webexteamssdk.aio.api.roles import AsyncRolesAPI
from webexteamssdk.aio.api.rooms import AsyncRoomsAPI
from webexteamssdk.aio.api.team_memberships import AsyncTeamMembershipsAPI
from webexteamssdk.aio.api.teams import AsyncTeamsAPI
from webexteamssdk.aio.api.webhooks import AsyncWebhooksAPI

from webexteamssdk.utils import check_type


class AsyncWebexTeamsAPI:
    """Webex Teams API wrapper.

    Creates a 'session' for all API calls through a created WebexTeamsAPI
    object.  The 'session' handles authentication, provides the needed headers,
    and checks all responses for error conditions.

    WebexTeamsAPI wraps all of the individual Webex Teams APIs and represents
    them in a simple hierarchical structure.
    """

    def __init__(
        self,
        access_token=None,
        base_url=DEFAULT_BASE_URL,
        single_request_timeout=DEFAULT_SINGLE_REQUEST_TIMEOUT,
        wait_on_rate_limit=DEFAULT_WAIT_ON_RATE_LIMIT,
        object_factory=immutable_data_factory,
        client_id=None,
        client_secret=None,
        oauth_code=None,
        redirect_uri=None,
        proxies=None,
    ):
        """Create a new WebexTeamsAPI object.

        An access token must be used when interacting with the Webex Teams API.
        This package supports three methods for you to provide that access
        token:

          1. You may manually specify the access token via the `access_token`
             argument, when creating a new WebexTeamsAPI object.

          2. If an access_token argument is not supplied, the package checks
             for a WEBEX_TEAMS_ACCESS_TOKEN environment variable.

          3. Provide the parameters (client_id, client_secret, oauth_code and
             oauth_redirect_uri) from your oauth flow.

        An AccessTokenError is raised if an access token is not provided
        via one of these two methods.

        Args:
            access_token(str): The access token to be used for API
                calls to the Webex Teams service.  Defaults to checking for a
                WEBEX_TEAMS_ACCESS_TOKEN environment variable.
            base_url(str): The base URL to be prefixed to the
                individual API endpoint suffixes.
                Defaults to webexteamssdk.DEFAULT_BASE_URL.
            single_request_timeout(int): Timeout (in seconds) for RESTful HTTP
                requests. Defaults to
                webexteamssdk.config.DEFAULT_SINGLE_REQUEST_TIMEOUT.
            wait_on_rate_limit(bool): Enables or disables automatic rate-limit
                handling. Defaults to
                webexteamssdk.config.DEFAULT_WAIT_ON_RATE_LIMIT.
            object_factory(callable): The factory function to use to create
                Python objects from the returned Webex Teams JSON data objects.
            client_id(str): The client id of your integration. Provided
                upon creation in the portal.
            client_secret(str): The client secret of your integration.
                Provided upon creation in the portal.
            oauth_code(str): The oauth authorization code provided by
                the user oauth process.
            oauth_redirect_uri(str): The redirect URI used in the user
                OAuth process.
            proxies(dict): Dictionary of proxies passed on to the requests
                session.

        Returns:
            WebexTeamsAPI: A new WebexTeamsAPI object.

        Raises:
            TypeError: If the parameter types are incorrect.
            AccessTokenError: If an access token is not provided via the
                access_token argument or an environment variable.

        """
        check_type(access_token, str, optional=True)
        check_type(base_url, str, optional=True)
        check_type(single_request_timeout, int, optional=True)
        check_type(wait_on_rate_limit, bool, optional=True)
        check_type(client_id, str, optional=True)
        check_type(client_secret, str, optional=True)
        check_type(oauth_code, str, optional=True)
        check_type(redirect_uri, str, optional=True)
        check_type(proxies, dict, optional=True)

        access_token = access_token or WEBEX_TEAMS_ACCESS_TOKEN

        # Init AccessTokensAPI wrapper early to use for oauth requests
        self.access_tokens = AsyncAccessTokensAPI(
            base_url, object_factory, single_request_timeout=single_request_timeout,
        )

        # Check if the user has provided the required oauth parameters
        oauth_param_list = [client_id, client_secret, oauth_code, redirect_uri]
        if not access_token and all(oauth_param_list):
            access_token = self.access_tokens.get(
                client_id=client_id,
                client_secret=client_secret,
                code=oauth_code,
                redirect_uri=redirect_uri,
            ).access_token

        # If an access token hasn't been provided as a parameter, environment
        # variable, or obtained via an OAuth exchange raise an error.
        if not access_token:
            raise AccessTokenError(
                "You must provide a Webex Teams access token to interact with "
                "the Webex Teams APIs, either via a WEBEX_TEAMS_ACCESS_TOKEN "
                "environment variable or via the access_token argument."
            )

        # Create the API session
        # All of the API calls associated with a WebexTeamsAPI object will
        # leverage a single RESTful 'session' connecting to the Webex Teams
        # cloud.
        self._session = AsyncRestSession(
            access_token=access_token,
            base_url=base_url,
            single_request_timeout=single_request_timeout,
            wait_on_rate_limit=wait_on_rate_limit,
            proxies=proxies,
        )

        # API wrappers
        self.people = AsyncPeopleAPI(self._session, object_factory)
        self.rooms = AsyncRoomsAPI(self._session, object_factory)
        self.memberships = AsyncMembershipsAPI(self._session, object_factory)
        self.messages = AsyncMessagesAPI(self._session, object_factory)
        self.teams = AsyncTeamsAPI(self._session, object_factory)
        self.team_memberships = AsyncTeamMembershipsAPI(self._session, object_factory)
        self.attachment_actions = AsyncAttachmentActionsAPI(
            self._session, object_factory
        )
        self.webhooks = AsyncWebhooksAPI(self._session, object_factory)
        self.organizations = AsyncOrganizationsAPI(self._session, object_factory)
        self.licenses = AsyncLicensesAPI(self._session, object_factory)
        self.roles = AsyncRolesAPI(self._session, object_factory)
        self.events = AsyncEventsAPI(self._session, object_factory)
        self.guest_issuer = AsyncGuestIssuerAPI(self._session, object_factory)

    @property
    def access_token(self):
        """The access token used for API calls to the Webex Teams service."""
        return self._session.access_token

    @property
    def base_url(self):
        """The base URL prefixed to the individual API endpoint suffixes."""
        return self._session.base_url

    @property
    def single_request_timeout(self):
        """Timeout (in seconds) for an single HTTP request."""
        return self._session.single_request_timeout

    @property
    def wait_on_rate_limit(self):
        """Automatic rate-limit handling enabled / disabled."""
        return self._session.wait_on_rate_limit

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._session.close()