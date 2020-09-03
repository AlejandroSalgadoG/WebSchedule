import pytz

def to_local_time(date):
    return pytz.timezone("Etc/GMT+5").localize( date )

def as_local_time(date):
    return date.astimezone( pytz.timezone('Etc/GMT+5') )
