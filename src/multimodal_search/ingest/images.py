"""Pick a sample of openaccess artworks with primary images + metadata."""
from __future__ import annotations
import pandas as pd
from ..config import RAW_DIR


def sample_image_rows(n: int, seed: int = 42, exclude: set[str] | None = None) -> pd.DataFrame:
    imgs = pd.read_csv(RAW_DIR / "published_images.csv", low_memory=False)
    imgs = imgs[(imgs["openaccess"] == 1) & (imgs["viewtype"] == "primary")]
    imgs = imgs.dropna(subset=["iiifthumburl", "depictstmsobjectid"])
    imgs = imgs.drop_duplicates(subset=["depictstmsobjectid"])
    if exclude:
        imgs = imgs[~imgs["uuid"].isin(exclude)]

    objects = pd.read_csv(RAW_DIR / "objects.csv", low_memory=False)
    df = imgs.merge(
        objects[["objectid", "title", "displaydate", "classification", "medium", "attribution"]],
        left_on="depictstmsobjectid", right_on="objectid", how="inner",
    )
    df = df.sample(n=min(n, len(df)), random_state=seed).reset_index(drop=True)
    return df[["uuid", "objectid", "iiifthumburl", "title", "displaydate",
               "classification", "medium", "attribution", "assistivetext"]]
