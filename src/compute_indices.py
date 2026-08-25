from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import typer
from shapely.geometry import Point, box

app = typer.Typer()


def shannon_entropy(counts: pd.Series) -> float:
    counts = counts[counts > 0]
    if counts.sum() == 0:
        return 0.0
    p = counts / counts.sum()
    return float(-np.sum(p * np.log(p)))


def pielou_evenness(counts: pd.Series) -> float:
    s = len(counts[counts > 0])
    if s <= 1:
        return 0.0
    return float(shannon_entropy(counts) / np.log(s))


def hill_number(counts: pd.Series, q: float) -> float:
    counts = counts[counts > 0]
    if counts.sum() == 0:
        return 0.0

    p = counts / counts.sum()

    if q == 1:
        return float(np.exp(shannon_entropy(counts)))

    return float(np.sum(p ** q) ** (1 / (1 - q)))


def make_grid(boundary: gpd.GeoDataFrame, grid_size_m: int) -> gpd.GeoDataFrame:
    boundary_proj = boundary.to_crs("EPSG:3857")
    minx, miny, maxx, maxy = boundary_proj.total_bounds

    cells = []
    ids = []
    i = 0

    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            cells.append(box(x, y, x + grid_size_m, y + grid_size_m))
            ids.append(i)
            i += 1
            y += grid_size_m
        x += grid_size_m

    grid = gpd.GeoDataFrame({"unit_id": ids}, geometry=cells, crs="EPSG:3857")

    boundary_union = boundary_proj.union_all()
    grid = grid[grid.intersects(boundary_union)].copy()
    grid["geometry"] = grid.geometry.intersection(boundary_union)

    return grid.to_crs("EPSG:4326")


def compute_metrics(joined: gpd.GeoDataFrame, unit_col: str, q_values: list[float]) -> pd.DataFrame:
    species_counts = joined.groupby(unit_col)["species"].value_counts()

    result = joined.groupby(unit_col).size().reset_index(name="observation_count")

    richness = (
        joined.groupby(unit_col)["species"]
        .nunique()
        .reset_index(name="species_richness")
    )
    result = result.merge(richness, on=unit_col, how="outer")

    shannon = (
        species_counts.groupby(level=0)
        .apply(shannon_entropy)
        .reset_index(name="shannon_entropy")
    )
    result = result.merge(shannon, on=unit_col, how="outer")

    evenness = (
        species_counts.groupby(level=0)
        .apply(pielou_evenness)
        .reset_index(name="pielou_evenness")
    )
    result = result.merge(evenness, on=unit_col, how="outer")

    for q in q_values:
        col = f"hill_q{str(q).replace('.', '_')}"
        hill = (
            species_counts.groupby(level=0)
            .apply(lambda counts: hill_number(counts, q))
            .reset_index(name=col)
        )
        result = result.merge(hill, on=unit_col, how="outer")

    return result


@app.command()
def main(
    occurrences_path: Path,
    output_path: Path|None = None,
    boundary_path: Path = typer.Option("data/raw/okinawa_boundary/N03-20250101_47.geojson"),
    mode: str = typer.Option("grid", help="'grid' or 'municipality'"),
    municipality_col: str = typer.Option("N03_004"),
    grid_size_m: int = typer.Option(5000),
    q_values: str = typer.Option("0,1,2"),
):
    sample_size = int(occurrences_path.stem.split("-")[-1].split("_")[0])
    if output_path is None:
        output_dir = Path("../data/processed")
        if mode == "municipality":
            fname = f"diversity-indices-municipality-N{sample_size}.parquet"
        elif mode == "grid":
            fname = f"diversity-indices-grid{grid_size_m}-N{sample_size}.parquet"
        output_path = output_dir /  fname
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(occurrences_path)

    points = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["decimalLongitude"], df["decimalLatitude"])],
        crs="EPSG:4326",
    )

    boundary = gpd.read_file(boundary_path).to_crs("EPSG:4326")

    if mode == "municipality":
        units = boundary.copy()
        units = units.rename(columns={municipality_col: "unit_id"})
        unit_col = "unit_id"

    elif mode == "grid":
        units = make_grid(boundary, grid_size_m=grid_size_m)
        unit_col = "unit_id"

    else:
        raise ValueError("mode must be 'grid' or 'municipality'")

    joined = gpd.sjoin(
        points,
        units[[unit_col, "geometry"]],
        how="inner",
        predicate="within",
    )

    q_list = [float(q.strip()) for q in q_values.split(",")]

    metrics = compute_metrics(joined, unit_col=unit_col, q_values=q_list)

    result = units.merge(metrics, on=unit_col, how="left")

    metric_cols = [c for c in result.columns if c not in ["unit_id", "geometry"]]
    for col in metric_cols:
        if pd.api.types.is_numeric_dtype(result[col]):
            result[col] = result[col].fillna(0)

    result.to_parquet(output_path, index=False)

    print(f"Saved: {output_path}")
    print(f"Rows: {len(result)}")
    print(f"Mode: {mode}")


if __name__ == "__main__":
    app()
