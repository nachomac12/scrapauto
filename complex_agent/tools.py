from typing import Any, List, Literal, Tuple, Dict
from infoparser.crud_auto import init_db, AutoDataBaseCRUD
from scraper.dolar import get_dolar_blue_value
from infoparser.schemas import DolarValues


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
            attributes[value] = {"possible_values": []}  # Corrected from key to value

    db: AutoDataBaseCRUD = await init_db()
    # Paso 2: Por cada atributo detectado, buscar en la base de datos todos los posibles valores para ese atributo
    for key in attributes.keys():
        values = await db.get_field_unique_values(key)
        attributes[key]["possible_values"] = values  # Corrected typo from posible_values to possible_values
    ret_val = ""
    for key, values in attributes.items():
        ret_val += f"{key}: {values}\n"
    return ret_val

async def aget_price_range(atributos: dict) -> Tuple[float, float]:
    """
    Given a list of attributes and possible values for each attribute, return the price range
    of cars that match any of those values for those attributes.
    For example:
    attributes = {
        "atributos": {
            "brand": ["Toyota", "TOYOTA"],
            "model": ["Corolla", "Corolla XL", "COROLLA", "Corolla XEI"],
            "year": ["2020", 2020],
            "version": ["1.8 XEI", "1.8"],
        }
    }
    """
    # Define required fields and provide default empty lists if missing
    required_fields = ["brand", "model", "year", "version"]
    for field in required_fields:
        if field not in atributos:
            atributos[field] = []  # Default to an empty list if the field is missing

    # Build a mongo filter based on OR conditions for each attribute and AND conditions for all attributes
    filter = {}
    for key, values in atributos.items():
        if len(values) == 0:
            continue
        filter[key] = {"$in": values}
        
    if not filter:
        return 0.0, 0.0

    db: AutoDataBaseCRUD = await init_db()
    print("-" * 20)
    print(filter)
    print("-" * 20)
    cars = await db.get_cars_by_filter(filter)
    prices = [car.precio for car in cars]

    if not prices:
        return 0.0, 0.0  # Return a default range if no prices are found

    return min(prices), max(prices)


async def aget_dolar_blue_value(rango_precio: Tuple[float, float]) -> DolarValues:
    """Transforma un rango de precio en un rango de precio en dolares"""
    return await get_dolar_blue_value()
