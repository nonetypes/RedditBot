# Functions for MetalGearQuoteBot
# get_reddit, quote_reply, match_quote, get_all_comments, get_replies,
# load_history, save_history, record_comment, similar_strings
# Last revised on 04/09/2021

from json import loads
from time import localtime
from threading import Thread, Timer
from difflib import SequenceMatcher


def auto_function(function, seconds, args=None, kwargs=None, threaded_function=False):
    """Call a function every x seconds. Timer is threaded.

    The function's given arguments (if applicable) are passed in a list:
    e.g. -> args=[arg1, arg2]
    The function's given keyword arguments are passed in a dictionary:
    e.g. -> kwargs={'kwarg_name': kwarg_val}

    threaded_function=True to call the function on its own thread.

    Uses Timer and Thread from threading library.
    """
    args = args if args is not None else []
    kwargs = kwargs if kwargs is not None else {}

    Timer(seconds, auto_function, [function, seconds],
          {'args': args, 'kwargs': kwargs, 'threaded_function': threaded_function}).start()

    if threaded_function:
        Thread(target=function, args=args, kwargs=kwargs).start()
    else:
        function(*args, **kwargs)


def similar_strings(string1, string2):
    """Tests the similarity between two strings.

    Returns a ratio, representing a percentage of similarity.

    https://stackoverflow.com/a/17388505
    """
    return SequenceMatcher(None, string1, string2).ratio()


def get_time(seconds=True, time=True, date=True):
    """Return the current time as a string in format '14:01:12'

    Uses time.localtime

    seconds=False -> '14:01'
    date=True -> '12-02-2020'
    date=True, time=True -> '12-02-2020 14:01:12'
    """
    current_time = ''
    # time.localtime() values must be formatted to have leading zeros
    current_time += str(localtime().tm_hour).zfill(2)
    current_time += f':{str(localtime().tm_min).zfill(2)}'
    if seconds:
        current_time += f':{str(localtime().tm_sec).zfill(2)}'
    if date:
        current_date = ''
        current_date += str(localtime().tm_mon).zfill(2)
        current_date += f'-{str(localtime().tm_mday).zfill(2)}'
        current_date += f'-{str(localtime().tm_year)}'
    if date and time:
        return f'{current_date} {current_time}'
    elif date:
        return current_date
    return current_time


if __name__ == '__main__':
    try:
        history = loads(open('ignore/history.json', 'r').read())
        print(f'Comments Posted: {len(history["comments"].keys())}')
    except Exception:
        pass
