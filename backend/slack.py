import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import config

client = WebClient(token=config.slackToken)


def sendSlackError(sApp, sError):
    client.chat_postMessage(channel='#cbcs-log',
                            text=f'{sApp} reports: {sError}')
