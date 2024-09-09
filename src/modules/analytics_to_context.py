"""Module for translating feedback data into the primary context for the RAG system."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.config import CONTEXT_TEMPLATE, PLOT_PALETTE, PRODUCT_NAME_COLUMN, N


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

    def prepare_marketplace_sentiment_data(
        self,
    ) -> pd.DataFrame:
        if "Review Date Month" not in self.data.columns:
            self.data["Review Date Month"] = self.data["Review Date"].dt.to_period("M")

        marketplace_sentiment_counts = self.data.groupby(
            ["Product Name", "Review Date Month", "Marketplace", "Sentiment", "Topic"]
        ).size()

        # Разворачивание данных: создание отдельных колонок для каждой тональности
        marketplace_sentiment_counts = marketplace_sentiment_counts.unstack(
            level="Sentiment", fill_value=0
        ).reset_index()

        return marketplace_sentiment_counts

    def create_product_topic_dict(
        self,
    ) -> dict:
        # Инициализация словаря
        product_topic_dict = {}

        # Группировка данных по продукту и топику
        grouped_data = self.data.groupby("Product Name")["Topic"].unique()

        # Заполнение словаря: продукт -> уникальные топики
        for product, topics in grouped_data.items():
            product_topic_dict[product] = list(topics)

        return product_topic_dict

    def find_most_negative_ratio_product(
        self,
    ) -> tuple:
        marketplace_sentiment_counts = self.prepare_marketplace_sentiment_data()

        # Группировка данных по продуктам и суммирование отзывов
        grouped_data = marketplace_sentiment_counts.groupby("Product Name").agg(
            {"Negative": "sum", "Positive": "sum", "Neutral": "sum"}
        )

        # Вычисление общего количества отзывов
        grouped_data["Total"] = (
            grouped_data["Negative"]
            + grouped_data["Positive"]
            + grouped_data["Neutral"]
        )

        # Вычисление отношения негативных отзывов к остальным (позитивные + нейтральные)
        grouped_data["Negative Ratio"] = grouped_data["Negative"] / (
            grouped_data["Total"]
        )

        # Поиск продукта с наибольшим отношением негативных отзывов
        most_negative_product = grouped_data["Negative Ratio"].idxmax()
        max_negative_ratio = grouped_data["Negative Ratio"].max()
        total_reviews = grouped_data.loc[most_negative_product, "Total"]

        return most_negative_product, max_negative_ratio, total_reviews

    def find_most_positive_ratio_product(
        self,
    ) -> tuple:
        marketplace_sentiment_counts = self.prepare_marketplace_sentiment_data()

        # Группировка данных по продуктам и суммирование отзывов
        grouped_data = marketplace_sentiment_counts.groupby("Product Name").agg(
            {"Negative": "sum", "Positive": "sum", "Neutral": "sum"}
        )

        # Вычисление общего количества отзывов
        grouped_data["Total"] = (
            grouped_data["Negative"]
            + grouped_data["Positive"]
            + grouped_data["Neutral"]
        )

        # Вычисление отношения позитивных отзывов к остальным (негативные + нейтральные)
        grouped_data["Positive Ratio"] = grouped_data["Positive"] / (
            grouped_data["Total"]
        )

        # Поиск продукта с наибольшим отношением позитивных отзывов
        most_positive_product = grouped_data["Positive Ratio"].idxmax()
        max_positive_ratio = grouped_data["Positive Ratio"].max()
        total_reviews = grouped_data.loc[most_positive_product, "Total"]

        return most_positive_product, max_positive_ratio, total_reviews

    def plot_review_trends(self, product: str, topic: str) -> None:
        marketplace_sentiment_counts = self.prepare_marketplace_sentiment_data()

        # Фильтрация данных для выбранного продукта и топика
        product_data = marketplace_sentiment_counts[
            marketplace_sentiment_counts["Product Name"] == product
        ]
        topic_data = product_data[product_data["Topic"] == topic]

        # Проверка на наличие данных
        if topic_data.empty:
            print(f"Нет данных для продукта '{product}' и топика '{topic}'")
            return

        # Преобразование данных в numpy массивы для корректного индексирования
        dates = topic_data["Review Date Month"].astype(str).values
        positive_reviews = topic_data["Positive"].values
        negative_reviews = topic_data["Negative"].values
        neutral_reviews = topic_data["Neutral"].values

        # Вычисление общего числа отзывов для нормализации
        total_reviews = positive_reviews + negative_reviews + neutral_reviews
        positive_percent = (positive_reviews / total_reviews) * 100
        negative_percent = (negative_reviews / total_reviews) * 100
        neutral_percent = (neutral_reviews / total_reviews) * 100

        # Построение графика
        fig, ax1 = plt.subplots(figsize=(10, 7))

        # Гистограмма для общего количества отзывов
        ax1.bar(dates, total_reviews, color="gray", alpha=0.3, label="Total Reviews")

        # График для процентных значений
        ax2 = ax1.twinx()
        ax2.plot(
            dates,
            positive_percent,
            label="Positive",
            marker="o",
            markersize=8,
            color=PLOT_PALETTE["Positive"],
            linewidth=2,
        )
        ax2.plot(
            dates,
            negative_percent,
            label="Negative",
            linestyle="--",
            marker="x",
            markersize=8,
            color=PLOT_PALETTE["Negative"],
            linewidth=2,
        )
        ax2.plot(
            dates,
            neutral_percent,
            label="Neutral",
            linestyle="-.",
            marker="s",
            markersize=8,
            color=PLOT_PALETTE["Neutral"],
            linewidth=2,
        )

        # Аннотирование графика процентных значений
        for i, value in enumerate(positive_percent):
            ax2.text(
                dates[i],
                value + 1,
                f"{value:.1f}%",
                ha="center",
                va="bottom",
                color=PLOT_PALETTE["Positive"],
                fontsize=9,
            )
        for i, value in enumerate(negative_percent):
            ax2.text(
                dates[i],
                value + 1,
                f"{value:.1f}%",
                ha="center",
                va="bottom",
                color=PLOT_PALETTE["Negative"],
                fontsize=9,
            )
        for i, value in enumerate(neutral_percent):
            ax2.text(
                dates[i],
                value + 1,
                f"{value:.1f}%",
                ha="center",
                va="bottom",
                color=PLOT_PALETTE["Neutral"],
                fontsize=9,
            )

        # Настройки графика
        ax2.set_title(
            f"Динамика процентного соотношения отзывов для продукта: {product},\n Топик: {topic}",
            fontsize=15,
            weight="bold",
        )
        ax2.set_xlabel("Месяц", fontsize=14)
        ax2.set_ylabel("Процент отзывов", fontsize=14)
        ax1.set_ylabel("Количество отзывов", fontsize=14)
        ax2.set_xticks(dates)
        ax2.set_xticklabels(dates, rotation=45, fontsize=12)
        ax2.tick_params(axis="y", labelsize=12)
        ax1.tick_params(axis="y", labelsize=12)
        ax2.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
        ax2.legend(loc="upper left", fontsize=12)
        ax1.legend(loc="upper right", fontsize=12)

        # Убираем лишние линии вокруг графика
        sns.despine()

        # Отображение графика
        plt.tight_layout()
        plt.show()

    def get_context_by_analytics(
        self,
    ) -> str:

        sentiment_percents = self.get_sentiment_percents()
        most_popular_products = self.get_most_popular_products()

        context = CONTEXT_TEMPLATE.format(
            self.username, sentiment_percents, self.marketplaces, most_popular_products
        )

        return context
