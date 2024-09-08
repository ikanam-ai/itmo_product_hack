"""Module for translating feedback data into the primary context for the RAG system."""

import pandas as pd

from src.config import CONTEXT_TEMPLATE, PRODUCT_NAME_COLUMN, N


class AnalyticsToContext:

    def __init__(self, data: pd.DataFrame) -> None:
        self.data = data.copy()
        self.username = self.data["Username"].unique()[0]
        self.marketplaces = self.data["Marketplace"].unique().tolist()

    def get_sentiment_percents(
        self,
    ) -> dict[str, float]:
        return (
            (self.data["Sentiment"].value_counts() / self.data["Sentiment"].shape[0])
            .round(2)
            .to_dict()
        )

    def get_most_popular_products(
        self,
    ) -> dict[str, int]:
        return self.data[PRODUCT_NAME_COLUMN].value_counts().head(N).to_dict()

    def get_context_by_analytics(
        self,
    ) -> str:

        sentiment_percents = self.get_sentiment_percents()
        most_popular_products = self.get_most_popular_products()

        context = CONTEXT_TEMPLATE.format(
            self.username, sentiment_percents, self.marketplaces, most_popular_products
        )

        return context
