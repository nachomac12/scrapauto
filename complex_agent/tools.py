from typing import Any, List, Literal, Tuple, Dict
from infoparser.crud_auto import init_db, AutoDataBaseCRUD


async def aget_car_attributes(
    atributos: List[
        Literal[
            "marca",
            "modelo",
            "year",
            "version",
            "color",
            "tipo_de_combustible",
            "puertas",
            "transmision",
            "motor",
            "tipo_de_carroceria",
            "kilometros",
            "direccion",
        ]
    ]
) -> dict:
    """
    Given a SimpleAuto object, return a dictionary with the car attributes
    based on brand, model, year, version, etc.

    input: ["brand", "model", "year", "version"]
    output: {
        "brand": {"possible_values": ["Toyota", "FORD", "TOYOTA", ...]},
        "model": {"possible_values": ["Corolla", "Focus", "Fiesta", ...]},
        "year": {"possible_values": ["2020", "2019", "2018", ...]},
        "version": {"possible_values": ["1.8 XEI", "1.6 XEI", "1.8 XLS", ...]},
    }
    """
    # Paso 1: Detectar todos los atributos de simple_auto que no sean None
    attributes = {}
    for value in atributos:
        if value in [
            "marca",
            "modelo",
            "year",
            "version",
            "color",
            "tipo_de_combustible",
            "puertas",
            "transmision",
            "motor",
            "tipo_de_carroceria",
            "kilometros",
            "direccion",
        ]:
            attributes[key] = {"possible_values": []}

    db: AutoDataBaseCRUD = await init_db()
    # Paso 2: Por cada atributo detectado, buscar en la base de datos todos los posibles valores para ese atributo
    for key in attributes.keys():
        values = await db.get_field_unique_values(key)
        attributes[key]["posible_values"] = values


async def aget_price_range(attributes: Dict[str, List[Any]]) -> Tuple[float, float]:
    """
    Given a list of attributes and poosible values for each attribute, return the price range
    of cars that match any of those valyes for those attributes.
    For example:
    attributes = {
        "brand": ["Toyota", "TOYOTA"],
        "model": ["Corolla", "Corolla XL", "COROLLA", "Corolla XEI"],
        "year": ["2020", 2020]},
        "version": ["1.8 XEI", "1.8"],
    }
    """
    # Build a mongo filter based on OR conditions for each attribute and AND conditions for all attributes
    filter = {}
    for key, values in attributes.items():
        filter[key] = {"$in": values}
    db: AutoDataBaseCRUD = await init_db()
    cars = await db.get_cars_by_filter(filter)
    prices = [car.precio for car in cars]
    return min(prices), max(prices)
