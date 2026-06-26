"""Load NGA CSVs and flatten each artwork into a single searchable document."""
from __future__ import annotations
import pandas as pd
from ..config import RAW_DIR


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / f"{name}.csv", low_memory=False)


def build_artwork_documents() -> pd.DataFrame:
    objects = _read("objects")
    constituents = _read("constituents")
    obj_const = _read("objects_constituents")

    artists = (
        obj_const.merge(constituents, on="constituentid", how="left")
        .groupby("objectid")["forwarddisplayname"]
        .apply(lambda s: ", ".join(sorted({x for x in s.dropna()})))
        .rename("artists")
    )

    df = objects.merge(artists, on="objectid", how="left")

    def to_doc(row) -> str:
        parts = [
            row.get("title"),
            f"by {row['artists']}" if pd.notna(row.get("artists")) else None,
            row.get("displaydate"),
            row.get("medium"),
            row.get("classification"),
            row.get("subclassification"),
            row.get("attribution"),
            row.get("attributioninverted"),
            row.get("visualbrowsertimespan"),
            row.get("visualbrowserclassification"),
            row.get("provenancetext"),
        ]
        return " | ".join(str(p).strip() for p in parts if pd.notna(p) and str(p).strip())

    df["document"] = df.apply(to_doc, axis=1)
    return df[["objectid", "title", "artists", "displaydate", "classification",
               "medium", "document"]].dropna(subset=["document"])
