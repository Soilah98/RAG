from hotel_rag import config
from hotel_rag.ingestion import load_sections
from hotel_rag.store import build_index

if __name__ == "__main__":
    sections = load_sections(config.DATA_DIR)
    n = build_index(sections)
    print(f"{n} rubriques indexées dans {config.CHROMA_DIR}")