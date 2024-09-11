from enum import Enum


class BaseEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)


class SupplyType(BaseEnum):
    ORIGIN = "產地"
    WHOLESALE = "批發"
    RETAIL = "零售"


class Category(BaseEnum):
    AGRICULTURE = "農產品"
    LIVESTOCK = "畜禽產品"
    FISHERY = "漁產品"


class ProductType(BaseEnum):
    # Agriculture
    RICE = "糧"
    VEGETABLE = "蔬菜"
    FRUIT = "水果"
    FLOWER = "花卉"

    # Livestock
    HOG = "豬"
    RAM = "羊"
    CHICKEN = "雞"
    DUCK = "鴨"
    GOOSE = "鵝"

    # Fishery
    FISH = "魚類"
    SHRIMP = "蝦類"
    SHELLFISH = "貝類"

    # Others
    OTHERS = "其他"


class LogLevel(BaseEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
