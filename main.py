# MetalGearQuoteBot by nonetypes
# Last revised on 04/07/2021
# A Reddit bot which replies to comments with an
# (in)appropriate quote from the Metal Gear Solid series.

from classes import MetalGearQuoteBot
from funcs import auto_function


stealth_mode = True

mg_quote_bot = MetalGearQuoteBot(stealth_mode)

# Minutes
fifteen = 15 * 60
sixty = 60 * 60

# The comment finding/quote posting part of the bot will run every 15 minutes.
# Every hour and on a separate threaded timer, the bot will look for poorly received
# quotes to delete.
auto_function(mg_quote_bot.delete_comments, sixty)
auto_function(mg_quote_bot.comment_search, fifteen)
