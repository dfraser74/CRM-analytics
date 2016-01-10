from datetime import date

from app.utils import weeks_between_two_date, get_interval_valid_dates
from app.utils.mixpanel import Mixpanel

__author__ = 'GHIBOUB Khalid'


class MixPanelService(object):
    def __init__(self, api_key, api_secret):
        super(MixPanelService, self).__init__()
        self.api = Mixpanel(
            api_key=api_key,
            api_secret=api_secret
        )

    def get_event_by_date(self, event, unit, interval, units=0):
        ee = self.api.request(['events', 'names'], {'type': 'unique'})
        data = self.api.request(['events'],
                                {'event': ee, 'unit': unit, 'interval': interval,
                                 'type': 'unique'}).get('data')
        result = []
        for item in data.get('series'):
            if units == 0:
                break
            result.append([data.get('values').get(event).get(item), item])
            units -= 1
        return result

    def weekly_new_users(self, start_date, end_date):
        today = str(date.today())
        interval = weeks_between_two_date(start_date, today)
        weeks = weeks_between_two_date(start_date, end_date)
        return self.get_event_by_date('SIGNED_UP_SUCCESS', 'week', interval, weeks)

    def daily_new_users(self, start_date, end_date):
        dates, interval = get_interval_valid_dates(end_date, start_date)
        return self.get_event_by_date('SIGNED_UP_SUCCESS', 'day', interval, dates)

    def daily_sign_in_clicks(self, start_date, end_date):
        dates, interval = get_interval_valid_dates(end_date, start_date)
        return self.get_event_by_date('SIGNIN_CLICK', 'day', interval, dates)

    def sign_in_clicker_and_users_ratio(self, start_date, end_date):
        sign_in_clickers = self.daily_sign_in_clicks(start_date, end_date)
        new_users = self.daily_new_users(start_date, end_date)
        result = []
        for index, user in enumerate(new_users):
            sign_in_clicker = sign_in_clickers[index]
            rate = 0 if sign_in_clicker[0] == 0 else float(int(user[0])) * 100 / sign_in_clicker[0]
            item = [round(rate, 2), user[1]]
            result.append(item)
        return result

    def active_users(self, start_date, end_date):
        units, interval = get_interval_valid_dates(end_date, start_date)
        resp = []
        result = self.get_active_users(interval, 1)
        keys = result.keys()
        keys.sort()
        for key in keys:
            if units == 0:
                break
            resp.append([result[key], key])
            units -= 1
        return resp

    def active_users_growth(self, start_date, end_date):
        units, interval = get_interval_valid_dates(end_date, start_date)
        resp = []
        result = self.get_active_users(interval, 1)
        keys = result.keys()
        keys.sort()
        last_key = None
        for key in keys:
            if units == 0:
                break
            if last_key:
                rate = ((result[key] - result[last_key]) * 100) / float(result[key])
                resp.append([rate, key])
            units -= 1
            last_key = key
        return resp

    def get_active_users(self, interval, actions):
        result = {}
        data = self.api.request(['events', 'properties'],
                                {'event': '$custom_event:100587', 'unit': 'day', 'interval': interval, 'name': 'email',
                                 'type': 'general'}).get('data')

        for email, actions_data in data.get('values').iteritems():
            for action_date, actions_count in actions_data.iteritems():
                if actions_count > actions:
                    result[action_date] = 1 if action_date not in result else result[action_date] + 1
        return result
