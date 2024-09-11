from typing import Final

N: Final[int] = 5

PRODUCT_NAME_COLUMN: Final[str] = "Product Name"
USERNAME_COLUMN: Final[str] = "Username"

CONTEXT_TEMPLATE: Final[str] = (
    """Название компании: {} \nРаспределение настроения отзывов на продукты компании в долях: {} \nКакие маркетплейсы фигурируют в собранных отзывах компании: {} \nТоп 5 самых популярных товаров по отзывам (формат "название продукта": количество отзывов в данных о компании): {}"""
)

PLOT_PALETTE: Final[dict[str, str]] = {
    "Positive": "#2ecc71",  # Зеленый
    "Negative": "#e74c3c",  # Красный
    "Neutral": "#3498db",  # Синий
}