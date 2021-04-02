# Functions for MetalGearQuoteBot
# quote_reply, match_quote, get_all_comments, get_replies

from quotes import quotes, triggers
from random import choice


def quote_reply(comment, quote_triggers):
    """Attempt to match quote_trigger terms to a comment. Not case sensitive.

    Collect multiple quotes in the event that theree are multiple trigger terms
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
        get_replies(child, all_comments, verbose=verbose)


if __name__ == '__main__':
    comments = ['This won\'t trigger a quote', 'Math Sucks! I like cigarettes.',
                'I bought some binoculars today.', 'I am looking forward to the Olympics.']
    for comment in comments:
        reply = quote_reply(comment, triggers)
        if reply is not None:
            print(f'Replying to "{comment}"')
            print(reply[1]+'\n')
