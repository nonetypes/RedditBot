# MetalGearQuoteBot by nonetypes
# Last revised on 04/03/2021
# A Reddit bot which replies to comments with an appropriate quote
# from the Metal Gear series.

from funcs import (quote_reply, match_quote, get_all_comments,
                   load_history, record_comment, similar_strings)
from quotes import triggers
from json import loads
from time import time
from praw import Reddit

# live should be True when ready to actually submit comments.
# live should be False for testing purposes. i.e. Bot functions in every way
# but will not submit replies. Used to see what would be replied to with what quote.
live = False

# List of subreddits to post in.
subreddits = ['metalgearsolid', 'metalgear', 'gaming']

# This is a list of usernames that this bot has posted under.
# Keep these accurate to avoid quote spamming.
bot_user_names = ['MetalGearQuoteBot']

# Keep track of stuff.
history = load_history()

# Bot account credentials are kept in a json object in separate folder and NOT uploaded to github.
bot_info = loads(open('ignore/bot_info.json', 'r').read())

reddit = Reddit(client_id=bot_info['client_id'],
                client_secret=bot_info['client_secret'],
                username=bot_info['username'],
                password=bot_info['password'],
                user_agent=bot_info['user_agent'])


for subreddit in subreddits:
    # Create a new history submission for a new subreddit.
    if subreddit not in history['subreddits'].keys():
        history['subreddits'][subreddit] = {"comments": [], "parents": [], "trigger_holds": {}}

    subreddit = reddit.subreddit(subreddit)
    # Limit submissions to the top ten hot page.
    for submission in subreddit.hot(limit=10):
        # Get all comments in the submission.
        submission_comments = get_all_comments(submission)
        # Refresh triggers for each submission.
        quote_triggers = triggers.copy()

        # Don't post a quote in a subreddit if it was posted in the last x hours.
        hours = 36
        for quote_name, time_posted in history['subreddits'][subreddit.display_name]['trigger_holds'].items():
            if time() - time_posted <= (60 * 60 * hours):
                quote_triggers[quote_name] = []

        # Check what quotes have already been posted in thread by bot so the
        # same quote won't be posted again, and do not reply to the same comment twice.
        do_not_reply = []
        for comment in submission_comments:
            if comment.author in bot_user_names:
                # Match the quote used in thread.
                quote_name = match_quote(comment.body)
                if quote_name is not None:
                    # Clear triggers for the quote.
                    quote_triggers[quote_name] = []
                # Take note of the parent comment id to not reply to the same comment twice.
                if comment.parent_id[:3] == 't1_':
                    do_not_reply.append(comment.parent_id[3:])
                else:
                    do_not_reply.append(comment.parent_id)

        # Walk through comments again, looking for comments to reply with a quote to.
        for comment in submission_comments:
            # Don't consider comments made by own bot, disregard comments which were already replied to,
            # and don't reply to a comment that is older than 10 hours.
            if (comment.author not in bot_user_names and comment.id not in do_not_reply
                    and time() - comment.created_utc <= (8 * 60 * 60)):
                # Attempt to match a quote trigger to the comment.
                mgs_quote = quote_reply(comment.body, quote_triggers)
                if mgs_quote is not None:
                    # Remove triggers so the same quote won't be used again in the same thread.
                    quote_triggers[mgs_quote[0]] = []
                    # Only post the reply if the quote is not in the comment.
                    # Also test if the quote and comment are not higher than a 90% match.
                    if (mgs_quote[1].lower() not in comment.body.lower() and
                            similar_strings(mgs_quote[1].lower(), comment.body.lower()) < .9):
                        if live:
                            reply = comment.reply(mgs_quote[1])
                            record_comment(comment, reply, subreddit, submission, mgs_quote[0], history)
                            # comment.upvote()
                            print('Posted comment in ', end='')
                        else:
                            print('Would have posted to ', end='')

                        # Print relevant info to see what was replied to.
                        print(f'r/{comment.subreddit}, "{submission.title}"')
                        print(f'Comment Link: https://reddit.com{comment.permalink}')
                        print('Comment: '+comment.body[:100].replace('\n', '')+'...')
                        print('Quote:   '+mgs_quote[1][:60]+'...\n')
