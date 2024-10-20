from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional


class AutoRaw(BaseModel):
    text: str = Field(title="Texto del anuncio")
    extracted: bool = Field(title="Si ya fue extraído o no", default=False)


class AutoRawDB(AutoRaw):
    id: str = Field(title="ID de la base de datos", alias="_id")
    extracted_car_id: Optional[str] = Field(title="ID del auto extraído", alias="extracted_car_id", default=None)
    created_at: datetime = Field(
        title="Fecha de creación",
        description="Fecha en la que se creó el registro",
    )
    updated_at: datetime = Field(
        title="Fecha de actualización",
        description="Fecha en la que se actualizó el registro",
    )


class SimpleAuto(BaseModel):
    precio: float = Field(title="Precio del auto")
    moneda: str = Field(title="Moneda del precio", description="Por ejemplo 'ARS', 'USD', etc. Si no se puede deducir, utilizar ARS por defecto.")
    url: str = Field(title="URL del anuncio")
    source: str = Field(
        title="Fuente del anuncio",
        description="Pagina web de donde se extrajo el anuncio, por ejemplo mercadolibre.com.ar",
    )
    external_id: str = Field(
        title="ID del anuncio en la fuente",
        description="ID del anuncio en la fuente, por ejemplo en mercadolibre.com.ar es el número que está al final de la URL",
    )
    marca: str = Field(title="Marca del auto")
    modelo: str = Field(title="Modelo del auto")
    year: str = Field(title="Año del auto")
    version: str = Field(
        title="Versión del auto",
        description="Por ejemplo '1.9 Sd Trendline 60b', 'CTV Pack', etc",
    )
    color: Optional[str] = Field(title="Color del auto")
    tipo_de_combustible: Optional[str] = Field(
        title="Tipo de combustible", description="Nafta, Diesel, etc"
    )
    puertas: Optional[str] = Field(
        title="Cantidad de puertas", description="2, 4, 5, etc"
    )
    transmision: Optional[str] = Field(
        title="Tipo de transmisión", description="Manual, Automática, etc"
    )
    motor: Optional[str] = Field(title="Motor del auto", description="1.6, 2.0, etc")
    tipo_de_carroceria: Optional[str] = Field(
        title="Tipo de carrocería", description="Sedán, Hatchback, etc"
    )
    kilometros: Optional[int] = Field(
        title="Kilómetros", description="Cantidad de kilómetros recorridos"
    )
    direccion: Optional[str] = Field(
        title="Tipo de dirección", description="Asistida, Mecánica, Hidráulica, etc"
    )
    other_info: Optional[str] = Field(
        title="Otra información",
        description="Cualquier otra información relevante del auto",
    )
    ignore: bool = Field(
        title="Si se debe ignorar el auto",
        description="Si se debe ignorar el auto en el caso de que el vendedor solo financie el auto en cuotas.",
    )


class SimpleAutoDB(SimpleAuto):
    id: str = Field(title="ID de la base de datos", alias="_id")
    created_at: datetime = Field(
        title="Fecha de creación",
        description="Fecha en la que se creó el registro",
    )
    updated_at: datetime = Field(
        title="Fecha de actualización",
        description="Fecha en la que se actualizó el registro",
    )


class DolarValues(BaseModel):
    """Valores del dolar para la venta."""
    blue: float = Field(title="Valor del dólar blue")
    oficial: float = Field(title="Valor del dólar oficial")
    mep: float = Field(title="Valor del dólar MEP/Bolsa")
    contado_con_liqui: float = Field(title="Valor del dólar contado con liqui")
    cripto: float = Field(title="Valor del dólar en criptomonedas")
    tarjeta: float = Field(title="Valor del dólar en tarjeta")
    

class DolarValuesDB(BaseModel):
    id: str = Field(title="ID de la base de datos", alias="_id")
    created_at: datetime = Field(title="Fecha de creación", description="Fecha en la que se creó el registro")


class OpenAIBatch(BaseModel):
    batch_id: str = Field(title="ID del batch")
    status: str = Field(title="Estado del batch")


class OpenAIBatchDB(OpenAIBatch):
    id: str = Field(title="ID de la base de datos", alias="_id")
    created_at: str = Field(title="Fecha de creación", description="Fecha en la que se creó el registro")
    updated_at: str = Field(title="Fecha de actualización", description="Fecha en la que se actualizó el registro")
