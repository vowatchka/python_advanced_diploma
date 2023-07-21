import sentry_sdk

from tweetty.api import create_api
from tweetty.settings import DEBUG

if not DEBUG:
    sentry_sdk.init(
        dsn="https://6bf414c310f6499b883242b257555c2e@o1137327.ingest.sentry.io/4505567241240576",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=1.0,
    )

app = create_api()
