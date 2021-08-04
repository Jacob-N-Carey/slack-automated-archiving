import os
import sys 
import datetime
import time 
import json 
import requests
from requests import api

from config import get_archiver_settings
from utils import get_logger

class Archiver():

    def __init__(self) -> None:
        self.settings = get_archiver_settings()
        self.logger = get_logger('archiver', './audit.log')

    def get_whitelist(self):
        keywords = []

        if os.path.isfile('whitelist.txt'):
            with open('whitelist.txt') as fc:
                keywords = fc.readlines()

        keywords = map(lambda x: x.strip(), keywords)
        whitelist = self.settings.get('whitelist')
        if whitelist:
            keywords = keywords + whitelist.split(',')
        
        return list(keywords)

    def get_channel_alert(self):
        archive_msg = f"This channel has been identified as inactive, and as such, is being archived. If you believe this is a mistake, the channel can be unarchived by a Slack Owner or Admin. You can find a list of your workspace's Owners and Admins <https://slack.com/help/articles/360003534892-Browse-people-and-user-groups-in-Slack|here>."

        channel_alert = {'channel_template': archive_msg}
        if os.path.isfile('templates.json'):
            with open('templates.json') as fc:
                channel_alert = json.load(fc)

        return channel_alert

    def api_handler(self, endpoint=None, payload=None, method='GET', retry=True, retry_delay=0):
        uri = f"https://slack.com/api/{endpoint}"
        payload['token'] = self.settings.get('token')

        try:
            if retry_delay > 0:
                time.sleep(retry_delay)

            if method == 'POST':
                response =  requests.post(uri, data=payload)
            else:
                response = requests.get(uri, payload)

            if response.status_code == requests.codes.ok and 'error' in response.json():
                self.logger.error(response.json()['error'])
                sys.exit(1)
            elif response.status_code == requests.codes.ok and response.json()['ok']:
                return response.json()
            elif response.status_code == requests.codes.too_many_requests:
                retry_timeout = float(response.headers['Retry-After'])
                return self.api_handler(endpoint, payload, method, False, retry_timeout)

        except Exception as error_msg:
            raise Exception(error_msg)
        return None

    def get_all_channels(self):
        payload = {'exclude_archived': 1}
        endpoint = 'channel.list'
        channels = self.api_handler(endpoint=endpoint, payload=payload)['channels']

        all_channels = []
        for c in channels:
            all_channels.append({
                'id': c['id'],
                'name': c['name'],
                'created': c['created'],
                'num_members': c['num_members']
            })

        return all_channels

    def get_most_recent_timestamp(self, channel_history, datetime_threshold):
        most_recent_datetime = datetime_threshold
        most_recent_bot_datetime = datetime_threshold

        if 'messages' not in channel_history:
            return (most_recent_datetime, False)

        for m in channel_history:
            if 'subtype' in m and m['subtype'] in self.settings.get('ignore_subtypes'):
                continue

            most_recent_datetime = datetime.datetime.fromtimestamp(float(m['ts']))
            break 

        if not most_recent_datetime:
            most_recent_bot_datetime = datetime.datetime.utcfromtimestamp(0)

        if datetime_threshold >= most_recent_bot_datetime > datetime_threshold:
            return( most_recent_bot_datetime, False)

        return (most_recent_datetime, True)

    def channel_disused(self, channel, datetime_threshold):
        endpoint = 'channels.history'
        num_members = channel['num_members']
        payload = {'channel': channel['id'], 'inclusive': 0, 'oldest': 0, 'count': 50}

        channel_history = self.api_handler(endpoint=endpoint, payload=payload)

        (most_recent_datetime, is_user) = self.get_most_recent_timestamp(channel_history, datetime.datetime.fromtimestamp(float(channel['created'])))

        min_members = self.settings.get('min_members')
        has_min_members = (min_members == 0 or min_members > num_members)

        return most_recent_datetime <= datetime_threshold and (not is_user or has_min_members)

    def channel_whitelisted(self, channel, white_listed_channels):
        endpoint = 'channels.info'
        payload = {'channel': channel['id']}
        channel_info = self.api_handler(endpoint=endpoint, payload=payload)

        channel_purpose = channel_info['channel']['purpose']['value']
        channel_topic = channel_info['channel']['topic']['value']
        if self.settings.get('ignore_channel_str') in channel_purpose or channel_topic:
            return True

        for wl_channel in white_listed_channels:
            wl_channel_name = wl_channel.strip('#')
            if wl_channel_name in channel['name']:
                return True

        return False 

    def send_message(self, channel_id, message):
        endpoint = 'chat.postMessage'
        payload = {
            'channel': channel_id,
            'user_name': 'archiver',
            'icon_emoji': ':ghost:',
            'text': message
        }

        self.api_handler(endpoint=endpoint, payload=payload, method='POST')

    def archive_channel(self, channel, alert):
        logger_message = f"Archiving channel {channel['name']}"
        self.logger.info(logger_message)

        channel_message = alert.format(self.settings.get('time_inactive'))
        self.send_message(channel['id'], channel_message)

        endpoint = 'channels.archive'
        payload = {'channel': channel['id']}

        self.api_handler(endpoint=endpoint, payload=payload)

    def send_admin_report(self, channels):
        if self.settings.get('admin_channel'):
            channel_names = ', '.join('#' + channel['name'] for channel in channels)
            admin_msg = f"Archiving {len(channels)} channels: {channel_names}"
            self.send_message(self.settings.get('admin_channel'), admin_msg)

    def main(self):
        whitelist = self.get_whitelist()
        alert = self.get_channel_alert()
        archived_channels = []

        for c in self.get_all_channels():
            sys.stdout.write('.')
            sys.stdout.flush()

            channel_whitelisted = self.channel_whitelisted(c, whitelist)
            channel_disused = self.channel_disused(c, self.settings.get('datetime_threshold'))

            if(not channel_whitelisted and channel_disused):
                archived_channels.append(c)
                self.archive_channel(c, alert['channel_template'])

        self.send_admin_report(archived_channels)


if __name__ == '__main__':
    ARCHIVER = Archiver()
    ARCHIVER.main()