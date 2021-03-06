import httplib2
from apiclient.discovery import build
from datetime import timedelta

from utils.str_opts import join_list
from flask.ext.restful import abort
from oauth2client import client

__author__ = 'GHIBOUB Khalid'


class GoogleAnalyticsService(object):
    def __init__(self, google_credential):
        g_credentials = client.OAuth2Credentials.from_json(google_credential.credential)
        http = httplib2.Http()
        if g_credentials.access_token_expired:
            g_credentials.refresh(http)
            google_credential.credential = g_credentials.to_json()
            google_credential.put()
        g_credentials.authorize(http)
        self.service = build('analytics', 'v3', http=http)

    def get_accounts(self):
        # Get a list of all Google Analytics accounts for this user
        return self.service.management().accounts().list().execute()

    def get_web_properties(self, account_id):
        # Get a list of all the properties for the specified account.
        return self.service.management().webproperties().list(accountId=account_id).execute()

    def get_profiles_list(self, account_id, proper):
        # Get a list of all views (profiles) for the specified property.
        return self.service.management().profiles().list(accountId=account_id, webPropertyId=proper).execute()

    def get_all_profiles_with_properties(self):
        # Get a list of all views (profiles) for the specified authenticated user.
        accounts = self.get_accounts().get('items')
        properties = []
        for account in accounts:
            account_id = account.get('id')
            web_properties = self.get_web_properties(account_id)
            for web_property in web_properties.get('items'):
                profiles_list = self.get_profiles_list(account_id, web_property.get('id'))
                profiles = {}
                for profile in profiles_list.get('items'):
                    profiles.update({profile.get('id'): profile.get('name')})
                properties.append(dict(websiteUrl=web_property.get('websiteUrl'), id=web_property.get('id'),
                                       profiles=profiles))
        return properties

    def get_data(self, profile_id, metrics_list, filters_list, dimensions_list, sorts_list, start_date, end_date):
        # Use the Analytics Service Object to query the Core Reporting API
        metrics = join_list(metrics_list) if len(metrics_list) else abort(500, message="you should provide metrics")
        filters = join_list(filters_list) if len(filters_list) else None
        dimensions = join_list(dimensions_list) if len(dimensions_list) else None
        sorts = join_list(sorts_list) if len(sorts_list) else None
        s_date = start_date.strftime('%Y-%m-%d')
        e_date = (end_date - timedelta(days=1)).strftime('%Y-%m-%d')
        return self.service.data().ga().get(
            ids='ga:' + profile_id,
            start_date=s_date,
            end_date=e_date,
            start_index=1,
            max_results=10000,
            dimensions=dimensions,
            metrics=metrics,
            sort=sorts,
            filters=filters).execute()

    def get_data_by_date(self, profile_id, metrics_list, filters_list, start_date, end_date):
        # Use the Analytics Service Object to query the Core Reporting API
        return self.get_data(profile_id, metrics_list, filters_list, ['date'], ['date'], start_date, end_date)

    def get_data_by_source(self, profile_id, metrics_list, filters_list, start_date, end_date):
        return self.get_data(profile_id, metrics_list, filters_list, ['source'], [], start_date, end_date)
