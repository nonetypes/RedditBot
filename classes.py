# MetalGearQuoteBot and child classes
# MetalGearQUoteBot, SubmitComments, DeleteBadKarma
# Last revised on 04/09/2021

from funcs import similar_strings, get_time
from quotes import quotes, triggers
from praw import Reddit
from praw.models import MoreComments
from json import loads, dumps
from random import choice
from time import time
from datetime import timedelta


class MetalGearQuoteBot:
    """Search "hot" submissions within subreddits for comments which contain specific
    triggers. When a trigger is found, a corresponding quote is posted.

    Once a quote is posted to a submission, it won't be posted to that submission again. Each quote
    is put into a holding period after it has been posted in which it will not be posted to the
    subreddit for x hours.

    A history is kept in /ignore/history.json to keep track of statistics on quotes posted.

    The bot can comb through comments that it posted to delete poorly received comments that have
    fallen below a given karma threshold.

    Set stealth_mode to True to test bot functionality without posting or deleting comments.
    """
    def __init__(self, stealth_mode=True, karma_threshold=-4):
        self.stealth_mode = stealth_mode
        self.karma_threshold = karma_threshold
        self.subreddits = ['metalgearsolid', 'metalgear', 'gaming']
        self.reddit = self.get_reddit()
        self.history = self.load_history()
        # This is a list of usernames that this bot has posted under. Keep these accurate to
        # reduce quote spamming regardless of how many people have or are using this bot.
        self.bot_user_names = ['MetalGearQuoteBot']

    def get_reddit(self):
        """Create and return a praw.Reddit object for doing reddit things.

        Bot account credentials are kept in a json object in separate
        folder and NOT uploaded to github.
        """
        bot_info = loads(open('ignore/bot_info.json', 'r').read())

        reddit = Reddit(client_id=bot_info['client_id'],
                        client_secret=bot_info['client_secret'],
                        username=bot_info['username'],
                        password=bot_info['password'],
                        user_agent=bot_info['user_agent'])

        return reddit

    def quote_reply(self, comment, quote_triggers):
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

    def comment_search(self):
        """Search for appropriate comments to reply to, then post a reply with a quote.
        """
        print(f'Beginning comment search at {get_time()}')
        for subreddit in self.subreddits:
            subreddit = self.reddit.subreddit(subreddit)

            # Create a new history submission for a new subreddit.
            if subreddit.display_name not in self.history['subreddits'].keys():
                self.history['subreddits'][subreddit.display_name] = {'comments': [], 'parents': [], 'holds': {}}

            # Limit submissions to the top x hot page.
            top_num = 20
            for submission in subreddit.hot(limit=top_num):
                # Get all comments in the submission.
                submission_comments = self.get_all_comments(submission)
                # Refresh triggers for each submission.
                quote_triggers = triggers.copy()

                # Don't post a quote in a subreddit if it was posted in the last x hours.
                hours = 72
                for quote_name, time_posted in self.history['subreddits'][subreddit.display_name]['holds'].items():
                    if time() - time_posted <= (hours * 60 * 60):
                        quote_triggers[quote_name] = []

                # Check what quotes have already been posted in thread by users (bot_user_names) using this code so the
                # same quote won't be posted again, and do not reply to the same comment twice.
                do_not_reply = []
                for comment in submission_comments:
                    if comment.author in self.bot_user_names:
                        # Match the quote used in thread.
                        quote_name = self.match_quote(comment.body)
                        if quote_name is not None:
                            # Clear triggers for the quote.
                            quote_triggers[quote_name] = []
                        # Take note of the parent comment id to not reply to the same comment twice.
                        if comment.parent_id[:3] == 't1_':
                            do_not_reply.append(comment.parent_id[3:])
                        else:
                            do_not_reply.append(comment.parent_id)
                    # In the event that a bot reply was deleted, be sure not to reply to the comment again.
                    if comment.id in self.history['parents']:
                        do_not_reply.append(comment.id)
                    if not self.stealth_mode:
                        # Upvote good comments.
                        if 'metalgearquotebot is dumb' in comment.body.lower():
                            comment.upvote()

                # Walk through comments again, looking for comments to reply with a quote to.
                for comment in submission_comments:
                    # Don't consider comments made by own bot, disregard comments which were already replied to,
                    # and don't reply to a comment that is older than x hours.
                    hours = 10
                    if (comment.author not in self.bot_user_names and comment.id not in do_not_reply
                            and time() - comment.created_utc <= (hours * 60 * 60)):
                        # Attempt to match a quote trigger to the comment.
                        mgs_quote = self.quote_reply(comment.body, quote_triggers)
                        if mgs_quote is not None:
                            # Remove triggers so the same quote won't be used again in the same thread.
                            quote_triggers[mgs_quote[0]] = []
                            # Only post the reply if the quote is not in the comment.
                            # And test if the quote and comment are not higher than a 90% match.
                            if (mgs_quote[1].lower() not in comment.body.lower() and
                                    similar_strings(mgs_quote[1].lower(), comment.body.lower()) < .9):
                                if not self.stealth_mode:
                                    reply = comment.reply(mgs_quote[1])
                                    # Keep track of things
                                    self.record_comment(comment, reply, subreddit, submission, mgs_quote[0])

                                    print('Posted comment in ', end='')
                                else:
                                    print('Would have posted to ', end='')

                                # Print relevant info to see what was replied to.
                                print(f'r/{comment.subreddit}, "{submission.title}"')
                                print(f'Comment Link: https://reddit.com{comment.permalink}')
                                print('Comment: '+comment.body[:100].replace('\n', '')+'...')
                                print('Quote:   '+mgs_quote[1][:60]+'...\n')

    def record_comment(self, parent, reply, subreddit, submission, quote_name):
        """Record comment information in history.json
        """
        self.history['parents'].append(parent.id)
        self.history['subreddits'][subreddit.display_name]['parents'].append(parent.id)
        # Record info of reply made by bot.
        if reply is not None:
            self.history['subreddits'][subreddit.display_name]['comments'].append(reply.id)
            self.history['subreddits'][subreddit.display_name]['holds'][quote_name] = reply.created_utc
            self.history['comments'][reply.id] = {'name': quote_name, 'time': reply.created_utc,
                                                  'subreddit': subreddit.display_name,
                                                  'submission': submission.id, 'parent': parent.id}
        self.save_history(self.history)

    def delete_comments(self):
        """Search through comments that the bot has posted and delete any that have been
        voted below a given threshold (default -4).

        stealth_mode=True during object creation will not result in comments being deleted.
        """
        print(f'Looking for bad comments to delete at {get_time()}')
        username = str(self.reddit.user.me())
        comments = self.reddit.redditor(username).comments.new(limit=None)
        for comment in comments:
            if comment.score <= self.karma_threshold:
                if not self.stealth_mode:
                    self.record_deletion(comment)
                    comment.delete()
                    print('Deleted a comment with score of ', end='')
                else:
                    print('Would have deleted a comment with score of ', end='')

                parent = self.reddit.comment(id=comment.parent_id[3:])
                print(f'{comment.score}: https://reddit.com{parent.permalink}')

    def record_deletion(self, comment):
        """Keep track of deleted comments in ignore/deleted.json.
        """
        try:
            deleted = loads(open('ignore/deleted.json', 'r').read())
        except FileNotFoundError:
            deleted = {'quotes': {}, 'tally': {}}
        finally:
            parent = self.reddit.comment(id=comment.parent_id[3:])
            quote_name = self.match_quote(comment.body)
            quote_age = time() - comment.created_utc
            quote_age = str(timedelta(seconds=quote_age))
            deleted['quotes'][parent.id] = {'Parent Link': f'https://reddit.com{parent.permalink}',
                                            'Quote ID': comment.id,
                                            'Quote Name': quote_name,
                                            'Quote': comment.body,
                                            'Quote Karma': comment.score,
                                            'Quote Age': quote_age}
            if not deleted['tally'][quote_name]:
                deleted['tally'][quote_name] = 1
            else:
                deleted['tally'][quote_name] += 1

            with open('ignore/deleted.json', 'w') as stream:
                stream.write(dumps(deleted))

    def get_all_comments(self, submission, verbose=False):
        """Collect every comment in a submission.
        Used with get_replies()

        https://stackoverflow.com/a/36377995
        """
        comments = submission.comments
        comments_list = []
        for comment in comments:
            # This is to ignore comments hiding in the "load more comments" button.
            if not isinstance(comment, MoreComments):
                self.get_replies(comment, comments_list, verbose=verbose)

        return comments_list

    def get_replies(self, comment, all_comments, verbose=False):
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

        for child in replies:
            # This is to ignore comments hiding in the "load more comments" button.
            if not isinstance(child, MoreComments):
                # Recursion. Get to the bottom of the comment tree.
                self.get_replies(child, all_comments, verbose=verbose)

    def load_history(self):
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

    def save_history(self, history):
        """Write the given history dictionary to ignore/history.json as a json object.
        """
        with open('ignore/history.json', 'w') as stream:
            stream.write(dumps(history))

    def match_quote(self, quote):
        """Match a given quote to a quote from the quotes.py collection.

        Return the quote name if matched, None otherwise.
        """
        for key, val in quotes.items():
            if quote in val:
                return key
        return None
