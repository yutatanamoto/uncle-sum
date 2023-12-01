# 毎日Mediumから特定のトピックの記事のサマリーをSLackに投稿するアプリケーションを作成します

import os
import fire
from medium_api import Medium
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

logger = logging.getLogger(__name__)

# We use unofficial API for Medium hosted on Rapid API via client library named medium-api
# Rapid API:  https://rapidapi.com/
# medium-api: https://medium-api.readthedocs.io/en/latest/index.html
RAPID_API_KEY = os.environ['RAPID_API_KEY']
QUERY = "Recommender System"

OPENAI_API_KEY = os.environ.get("MOTTY_OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
OPENAPI_SYSTEM_CONTEXT = """与えられた記事について、以下の制約条件をもとに要約を出力してください。
    制約条件:
    ・文章は簡潔にわかりやすく。
    ・マークダウン形式の箇条書き3行で出力。
    ・要約した文章は日本語へ翻訳。
    ・最終的な結論を含めること。

    期待する出力フォーマット:
    1.
    2.
    3."""

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]


class Article:
    def __init__(self, url: str, title: str, markdown_content: str):
        self.url = url
        self.title = title
        self.markdown_content = markdown_content
        self.markdown_summary = None

def get_articles() -> list[Article]:
    medium = Medium(RAPID_API_KEY)
    results = medium.search_articles(query=QUERY)
    return [Article(url=result.info["url"], title=result.info["title"], markdown_content=result.markdown) for result in results[-10:]]

def summarize(text: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {'role': 'system', 'content': OPENAPI_SYSTEM_CONTEXT},
            {'role': 'user', 'content': text},
        ],
        temperature=0.25,
    )
    return response['choices'][0]['message']['content']

def send_to_slack(article: Article) -> None:
    client = WebClient(token=SLACK_BOT_TOKEN)
    client.chat_postMessage(
        channel="C0431NG38JC",
        blocks=[
               		{
               			"type": "section",
               			"text": {
               				"type": "mrkdwn",
               				"text": article.title
               			}
               		},
               		{
               			"type": "divider"
               		},
               		{
               			"type": "section",
               			"text": {
               				"type": "mrkdwn",
               				"text": article.markdown_summary
               			}
               		},
               		{
               			"type": "section",
               			"text": {
               				"type": "mrkdwn",
               				"text": f"ref: {article.url}"
               			}
               		}
               	]
    )

def main():
    articles = get_articles()
    for article in articles:
        logger.info("summarize and send")
        article.markdown_summary = summarize(article.markdown_content)
        send_to_slack(article)

if __name__ == "__main__":
    fire.Fire(main)
