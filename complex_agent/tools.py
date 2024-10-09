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
        attributes[key][
            "possible_values"
        ] = values  # Corrected typo from posible_values to possible_values

    return attributes

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
    original_prices = [
        {"value": car.precio, "moneda": car.moneda, "id": car.id} for car in cars
    ]

    if not original_prices:
        return 0.0, 0.0  # Return a default range if no prices are found

    # Dolar price:
    dolar_values: DolarValues = await get_dolar_blue_value()

    prices_ars = []
    prices_usd = []
    # For price dict in prices, if moneda is USD, convert to ARS using dolar_values.blue
    for price_dict in original_prices:
        if price_dict["moneda"] == "USD":
            prices_usd.append(price_dict)
            converted_price_dict = price_dict.copy()
            converted_price_dict["moneda"] = "ARS"
            converted_price_dict["value"] = price_dict["value"] * float(
                dolar_values.blue
            )
            prices_ars.append(converted_price_dict)
        elif price_dict["moneda"] == "ARS":
            prices_ars.append(price_dict)
            converted_price_dict = price_dict.copy()
            converted_price_dict["moneda"] = "USD"
            converted_price_dict["value"] = price_dict["value"] / float(
                dolar_values.blue
            )
            prices_usd.append(converted_price_dict)
        else:
            raise ValueError(f"Moneda no reconocida: {price_dict['moneda']}")
        
    # Get the price_dict for the min value and max value
    min_price_dict_ars = min(prices_ars, key=lambda x: x["value"])
    max_price_dict_ars = max(prices_ars, key=lambda x: x["value"])

    min_price_dict_usd = min(prices_usd, key=lambda x: x["value"])
    max_price_dict_usd = max(prices_usd, key=lambda x: x["value"])

    return {
        "min_price_value_ars": min_price_dict_ars["value"],
        "min_price_currency_ars": min_price_dict_ars["moneda"],
        "min_price_car_id_ars": min_price_dict_ars["id"],
        "max_price_value_ars": max_price_dict_ars["value"],
        "max_price_currency_ars": max_price_dict_ars["moneda"],
        "max_price_car_id_ars": max_price_dict_ars["id"],
        "min_price_value_usd": min_price_dict_usd["value"],
        "min_price_currency_usd": min_price_dict_usd["moneda"],
        "min_price_car_id_usd": min_price_dict_usd["id"],
        "max_price_value_usd": max_price_dict_usd["value"],
        "max_price_currency_usd": max_price_dict_usd["moneda"],
        "max_price_car_id_usd": max_price_dict_usd["id"],
    }
