# MetalGearQuoteBot by nonetypes
# Last revised on 04/04/2021
# A Reddit bot which replies to comments with an
# (in)appropriate quote from the Metal Gear series.

from funcs import (get_reddit, quote_reply, match_quote, get_all_comments,
                   load_history, record_comment, similar_strings)
from quotes import triggers
from time import time

# live should be True when ready to actually submit comments.
# live should be False for testing purposes. i.e. Bot functions in every way
# but will not submit replies. Used to see what would be replied to with what quote.
# live = True
live = False

# List of subreddits to post in.
subreddits = ['metalgearsolid', 'metalgear', 'gaming']

# This is a list of usernames that this bot has posted under.
# Keep these accurate to reduce quote spamming regardless of how
# many people have or are using this bot.
bot_user_names = ['MetalGearQuoteBot']

# Keep track of stuff.
history = load_history()

# Create praw.Reddit object using bot credentials from /ignore/bot_info
reddit = get_reddit()


for subreddit in subreddits:
    subreddit = reddit.subreddit(subreddit)

    # Create a new history submission for a new subreddit.
    if subreddit.display_name not in history['subreddits'].keys():
        history['subreddits'][subreddit.display_name] = {'comments': [], 'parents': [], 'trigger_holds': {}}

    # Limit submissions to the top x hot page.
    top_num = 20
    for submission in subreddit.hot(limit=top_num):
        # Get all comments in the submission.
        submission_comments = get_all_comments(submission)
        # Refresh triggers for each submission.
        quote_triggers = triggers.copy()

        # Don't post a quote in a subreddit if it was posted in the last x hours.
        hours = 48
        for quote_name, time_posted in history['subreddits'][subreddit.display_name]['trigger_holds'].items():
            if time() - time_posted <= (hours * 60 * 60):
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
            # and don't reply to a comment that is older than x hours.
            hours = 10
            if (comment.author not in bot_user_names and comment.id not in do_not_reply
                    and time() - comment.created_utc <= (hours * 60 * 60)):
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
                            print('Posted comment in ', end='')
                        else:
                            print('Would have posted to ', end='')

                        # Print relevant info to see what was replied to.
                        print(f'r/{comment.subreddit}, "{submission.title}"')
                        print(f'Comment Link: https://reddit.com{comment.permalink}')
                        print('Comment: '+comment.body[:100].replace('\n', '')+'...')
                        print('Quote:   '+mgs_quote[1][:60]+'...\n')
