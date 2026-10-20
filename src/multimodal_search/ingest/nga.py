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
    images = _read("published_images")

    artists = (
        obj_const.merge(constituents, on="constituentid", how="left")
        .groupby("objectid")["forwarddisplayname"]
        .apply(lambda s: ", ".join(sorted({x for x in s.dropna()})))
        .rename("artists")
    )

    primary = images[images["viewtype"] == "primary"].dropna(subset=["assistivetext"])
    alt = (
        primary.drop_duplicates(subset=["depictstmsobjectid"])
        .set_index("depictstmsobjectid")["assistivetext"]
        .rename("assistivetext")
    )

    primary_open = images[(images["openaccess"] == 1) & (images["viewtype"] == "primary")].dropna(
        subset=["uuid", "depictstmsobjectid"]
    )
    iiif_map = (
        primary_open.drop_duplicates(subset=["depictstmsobjectid"])
        .set_index("depictstmsobjectid")["uuid"]
        .apply(lambda u: f"https://api.nga.gov/iiif/{u}/full/!600,600/0/default.jpg")
        .rename("iiif")
    )

    try:
        terms_df = _read("objects_terms")
        terms_clean = terms_df[
            ~terms_df["term"].isin(["Keywords", "Themes", "School", "Technique", "Style"])
        ].dropna(subset=["term"])
        terms = (
            terms_clean.groupby("objectid")["term"]
            .apply(lambda s: ", ".join(sorted(set(s))))
            .rename("terms")
        )
    except Exception:
        terms = pd.Series(dtype=object, name="terms")

    df = objects.merge(artists, on="objectid", how="left")
    df = df.merge(alt, left_on="objectid", right_index=True, how="left")
    df = df.merge(iiif_map, left_on="objectid", right_index=True, how="left")
    df = df.merge(terms, left_on="objectid", right_index=True, how="left")

    def to_doc(row) -> str:
        parts = [
            row.get("title"),
            f"by {row['artists']}" if pd.notna(row.get("artists")) else None,
            row.get("displaydate"),
            row.get("medium"),
            row.get("classification"),
            row.get("subclassification"),
            row.get("assistivetext"),
            f"Subjects: {row['terms']}" if pd.notna(row.get("terms")) else None,
            row.get("attribution"),
            row.get("attributioninverted"),
            row.get("visualbrowsertimespan"),
            row.get("visualbrowserclassification"),
            row.get("provenancetext"),
        ]
        return " | ".join(str(p).strip() for p in parts if pd.notna(p) and str(p).strip())

    df["document"] = df.apply(to_doc, axis=1)
    return df[
        ["objectid", "title", "artists", "displaydate", "classification",
         "medium", "iiif", "document"]
    ].dropna(subset=["document"])
