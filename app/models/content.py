from typing import Annotated, Literal
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class TextContent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    type: Literal["text"]
    text: str = Field(min_length=1)


class LinkContent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    type: Literal["link"]
    label: str = Field(min_length=1)
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def no_credentials(cls, value):
        if value.username or value.password:
            raise ValueError("Los enlaces no deben incluir credenciales.")
        return value


class FileContent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    file: str = Field(min_length=1)

    @field_validator("file")
    @classmethod
    def safe_relative_path(cls, value):
        parts = value.split("/")
        if len(parts) < 2 or any(part in ("", ".", "..") for part in parts):
            raise ValueError("Usa una ruta relativa dentro de documents/ o images/.")
        if any(character in value for character in "\\:%?#") or any(ord(c) < 32 for c in value):
            raise ValueError("La ruta del archivo contiene caracteres no permitidos.")
        return value


class DocumentContent(FileContent):
    type: Literal["document"]
    label: str = Field(min_length=1)

    @field_validator("file")
    @classmethod
    def document_extension(cls, value):
        if not value.startswith("documents/") or PurePosixPath(value).suffix.lower() not in {
            ".pdf", ".txt", ".docx", ".xlsx", ".pptx"
        }:
            raise ValueError("Documento permitido: PDF, TXT, DOCX, XLSX o PPTX dentro de documents/.")
        return value


class ImageContent(FileContent):
    type: Literal["image"]
    alt: str = "Imagen de la conversación"

    @field_validator("file")
    @classmethod
    def image_extension(cls, value):
        if not value.startswith("images/") or PurePosixPath(value).suffix.lower() not in {
            ".png", ".jpg", ".jpeg", ".gif", ".webp"
        }:
            raise ValueError("Imagen permitida: PNG, JPG, GIF o WEBP dentro de images/.")
        return value


Content = Annotated[TextContent | LinkContent | DocumentContent | ImageContent, Field(discriminator="type")]
