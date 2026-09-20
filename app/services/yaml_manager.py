from pathlib import Path
import os
import tempfile

import yaml

from app.models.knowledge import Knowledge


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys instead of silently overwriting nodes."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError("Todas las claves YAML deben ser texto.")
        if key in result:
            raise ValueError(f"Clave YAML duplicada: {key!r}.")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


class YamlManager:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Knowledge:
        try:
            with self.path.open(encoding="utf-8") as stream:
                return Knowledge.model_validate(yaml.load(stream, Loader=UniqueKeyLoader))
        except (OSError, ValueError, yaml.YAMLError) as error:
            raise ValueError(f"No se pudo cargar {self.path}: {error}") from error

    def save(self, knowledge: Knowledge):
        """Replace only after a complete validated UTF-8 YAML has been written."""
        content = yaml.safe_dump(knowledge.model_dump(mode="json", exclude_none=True),
                                 allow_unicode=True, sort_keys=False)
        descriptor, temporary = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
