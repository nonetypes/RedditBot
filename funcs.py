# Functions for MetalGearQuoteBot
# quote_reply, match_quote, get_all_comments, get_replies
# Last revised on 04/03/2021

from quotes import quotes, triggers
from json import loads, dumps
from random import choice
from difflib import SequenceMatcher
from praw.models import MoreComments


def quote_reply(comment, quote_triggers):
    """Attempt to match quote_trigger terms to a comment. Not case sensitive.

    Collect multiple quotes in the event that there are multiple trigger terms
    within a comment. Return one of the quotes at random.

    Returns a tuple of (quote_name, quote), or returns None if no matches were found.
    """
    replies = []
    for quote, trigger in quote_triggers.items():
        for term in trigger:
            if term in comment.lower():
                # If there are multiple quotes associated with a term, pick one at random.
                if isinstance(quotes[quote], list):
                    replies.append((quote, choice(quotes[quote])))
                else:
                    replies.append((quote, quotes[quote]))

    if replies:
        return(choice(replies))
    else:
        return None


def match_quote(quote):
    """Match a given quote to a quote from the quotes.py collection.

    Return the quote name if matched, None otherwise.
    """
    for key, val in quotes.items():
        if quote in val:
            return key
    return None

def get_all_comments(submission, verbose=False):
    """Collect every comment in a submission.
    Used with get_replies()

    https://stackoverflow.com/a/36377995
    """
    comments = submission.comments
    comments_list = []
    for comment in comments:
        # This is to ignore comments hiding in the "load more comments" button.
        if not isinstance(comment, MoreComments):
            get_replies(comment, comments_list, verbose=verbose)

    return comments_list


def get_replies(comment, all_comments, verbose=False):
    """Collect every reply from a comment.
    Used with get_all_comments() to collect every comment in a submission.

    https://stackoverflow.com/a/36377995
    """
    all_comments.append(comment)
    if not hasattr(comment, "replies"):
        replies = comment.comments()
        if verbose:
            print("fetching (" + str(len(all_comments)) + " comments fetched total)")
    else:
        replies = comment.replies

    # Recursion. Get to the bottom of the comment tree.
    for child in replies:
        # This is to ignore comments hiding in the "load more comments" button.
        if not isinstance(child, MoreComments):
            get_replies(child, all_comments, verbose=verbose)


def record_comment(parent, reply, subreddit, submission, quote_name, history):
    """Record comment information in history.json
    """
    history['parents'].append(parent.id)
    history['subreddits'][subreddit.display_name]['parents'].append(parent.id)
    # Record info of reply made by bot.
    if reply is not None:
        history['subreddits'][subreddit.display_name]['comments'].append(reply.id)
        history['subreddits'][subreddit.display_name]['trigger_holds'][quote_name] = reply.created_utc
        history['comments'][reply.id] = {'name': quote_name, 'time': reply.created_utc,
                                        'subreddit': subreddit.display_name,
                                        'submission': submission.id, 'parent': parent.id}
    save_history(history)


def load_history():
    """Attempt to load ignore/history.json as a dictionary then return it.

    If a FileNotFoundError is encountered, a blank history dictionary will be returned.

    Any other error encountered will return None.
    """
    try:
        history = loads(open('ignore/history.json', 'r').read())
    except FileNotFoundError:
        print('ERROR: ignore/history.json not found')
        print('Creating new history...')
        return {"subreddits": {}, "comments": {}, "parents": []}
    except Exception as error:
        print(f'ERROR: Could not load history.json -- {error}')
        return None
    else:
        return history


def save_history(history):
    """Write the given history dictionary to ignore/history.json as a json object.
    """
    with open('ignore/history.json', 'w') as stream:
        stream.write(dumps(history))


def similar_strings(string1, string2):
    """Tests the similarity between two strings.

    Returns a ratio, representing a percentage of similarity.

    https://stackoverflow.com/a/17388505
    """
    return SequenceMatcher(None, string1, string2).ratio()


if __name__ == '__main__':
    comments = ['This won\'t trigger a quote', 'Math Sucks! I like cigarettes.',
                'I bought some binoculars today.', 'I am looking forward to the Olympics.']
    for comment in comments:
        reply = quote_reply(comment, triggers)
        if reply is not None:
            print(f'Replying to "{comment}"')
            print(reply[1]+'\n')
