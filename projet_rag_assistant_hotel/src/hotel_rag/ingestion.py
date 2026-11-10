from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class Section:
    source: str
    title: str
    text: str

    @property
    def markdown(self) -> str:
        return f"## {self.title}\n\n{self.text}"


def load_sections(data_dir: Path) -> list[Section]:
    """Une page de PDF = une rubrique : 1re ligne = titre, dernière ligne = pied de page."""
    pdf_paths = sorted(data_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"Aucun PDF dans {data_dir}")

    sections = []
    for path in pdf_paths:
        for page in PdfReader(path).pages:
            lines = (page.extract_text() or "").split("\n")
            sections.append(Section(path.name, lines[0], "\n".join(lines[1:-1])))
    return sections