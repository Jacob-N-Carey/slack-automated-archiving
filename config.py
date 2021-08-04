import os
import datetime

def get_archiver_settings():
    time_inactive = int(os.environ.get('TIME_INACTIVE', 180))
    return {
        'admin_channel': os.environ.get('ADMIN_CHANNEL', ''),
        'time_inactive': time_inactive,
        'min_members': int(os.environ.get('MIN_MEMBERS', 0)),
        'token': os.environ.get('TOKEN', ''),
        'datetime_threshold': (datetime.datetime.now() - datetime.timedelta(days=time_inactive)),
        'whitelist': os.environ.get('WHITELIST', ''),
        'ignore_subtypes': {'channel_leave', 'channel_join'},
        'ignore_channel_str': os.environ.get('IGNORE_PURPOSE', '%noarchive')
    }