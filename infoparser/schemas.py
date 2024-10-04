from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class AutoRaw(BaseModel):
    text: str = Field(title="Texto del anuncio")
    extracted: bool = Field(title="Si ya fue extraído o no", default=False)


class AutoRawDB(BaseModel):
    id: str = Field(title="ID de la base de datos", alias="_id")
    created_at: datetime = Field(
        title="Fecha de creación",
        description="Fecha en la que se creó el registro",
    )
    updated_at: datetime = Field(
        title="Fecha de actualización",
        description="Fecha en la que se actualizó el registro",
    )


class SimpleAuto(BaseModel):
    url: str = Field(title="URL del anuncio")
    source: str = Field(
        title="Fuente del anuncio",
        description="Pagina web de donde se extrajo el anuncio, por ejemplo mercadolibre.com.ar",
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


class SimpleAutoDB(SimpleAuto):
    id: str = Field(title="ID de la base de datos", alias="_id")
    extracted_at: datetime = Field(
        title="Fecha de extracción",
        description="Fecha en la que se extrajo la información",
    )
    created_at: datetime = Field(
        title="Fecha de creación",
        description="Fecha en la que se creó el registro",
    )
    updated_at: datetime = Field(
        title="Fecha de actualización",
        description="Fecha en la que se actualizó el registro",
    )
    raw_source_id: str = Field(
        title="ID de la fuente cruda",
        description="ID de la fuente cruda de donde se extrajo la información",
    )
