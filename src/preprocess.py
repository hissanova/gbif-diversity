from pathlib import Path
import pandas as pd
import typer

app = typer.Typer()


DEFAULT_COLS = [
    "key",
    "scientificName",
    "species",
    "genus",
    "family",
    "order",
    "class",
    "phylum",
    "kingdom",
    "decimalLatitude",
    "decimalLongitude",
    "eventDate",
    "year",
    "basisOfRecord",
]


@app.command()
def main(
    input_path: Path,
    output_path: Path | None = typer.Option(None),
    min_year: int | None = typer.Option(None),
    max_year: int | None = typer.Option(None),
    drop_duplicates: bool = typer.Option(True),
):
    if output_path is None:
        output_dir = Path("../data/processed")
        output_path = output_dir / (input_path.stem + "_cleaned.parquet")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(input_path)

    cols = [c for c in DEFAULT_COLS if c in df.columns]
    df = df[cols].copy()

    df = df.dropna(subset=["decimalLatitude", "decimalLongitude", "species"])

    if "year" in df.columns:
        if min_year is not None:
            df = df[df["year"] >= min_year]
        if max_year is not None:
            df = df[df["year"] <= max_year]

    if drop_duplicates:
        df = df.drop_duplicates()

    df.to_parquet(output_path, index=False)

    print(f"Saved: {output_path}")
    print(f"Shape: {df.shape}")


if __name__ == "__main__":
    app()
