# MetalGearQuoteBot by nonetypes
# Last revised on 04/02/2021
# A Reddit bot which replies to comments with an appropriate quote
# from the Metal Gear series.

from funcs import quote_reply, match_quote, get_all_comments
from quotes import triggers
from json import loads
import praw

# live should be True when ready to actually submit comments.
# live should be False for testing purposes. i.e. Bot functions in every way
# but will not submit replies. Used to see what would be replied to with what quote.
live = False

# List of subreddits to post in.
subreddits = ['mechanicalMercs', 'metalgearsolid']

# Keep this accurate.
bot_user_name = 'MetalGearQuoteBot'

# Bot account credentials are kept in a json object in separate folder and NOT uploaded to github.
bot_info = loads(open('ignore/bot_info.json', 'r').read())

reddit = praw.Reddit(client_id=bot_info['client_id'],
                     client_secret=bot_info['client_secret'],
                     username=bot_info['username'],
                     password=bot_info['password'],
                     user_agent=bot_info['user_agent'])


for subreddit in subreddits:
    subreddit = reddit.subreddit(subreddit)

    # Limit submissions to the top ten hot page.
    for submission in subreddit.hot(limit=10):
        # Get all comments in the submission.
        submission_comments = get_all_comments(submission)
        # Refresh triggers for each submission.
        quote_triggers = triggers.copy()

        # First, check what quotes have already been posted in thread by bot so the
        # same quote won't be posted again, and do not reply to the same comment twice.
        do_not_reply = []
        for comment in submission_comments:
            if comment.author == bot_user_name:
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
            # Don't consider comments made by own bot, and disregard comments which were already replied to.
            if comment.author != bot_user_name and comment.id not in do_not_reply:
                # Attempt to match a quote trigger to the comment.
                mgs_quote = quote_reply(comment.body, quote_triggers)
                if mgs_quote is not None:
                    # Remove triggers so the same quote won't be used again in the same thread.
                    quote_triggers[mgs_quote[0]] = []
                    # Only post the reply if the quote is not in the comment.
                    # i.e. if a redditor has posted a comment containing one of the MG quotes in quotes.py
                    if mgs_quote[1].lower() not in comment.body.lower():
                        if live:
                            comment.reply(mgs_quote[1])
                            # comment.upvote()
                            print('Posted comment in ', end='')
                        else:
                            print('Would have posted to ', end='')

                        # Print relevant info to see what was replied to.
                        print(f'/r/{comment.subreddit}, "{submission.title}"')
                        print('Comment: '+comment.body[:100].replace('\n', '')+'...')
                        print('Quote:   '+mgs_quote[1][:60]+'...\n')
