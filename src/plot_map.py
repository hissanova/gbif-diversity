from pathlib import Path
import json
import geopandas as gpd
import plotly.express as px
import typer

app = typer.Typer()


@app.command()
def main(
    input_path: Path,
    output_dir: Path = typer.Option("../outputs/maps"),
    id_col: str = typer.Option("unit_id"),
    columns: str = typer.Option(
        "observation_count,species_richness,shannon_entropy,pielou_evenness,hill_q1_0,hill_q2_0"
    ),
    center_lat: float = typer.Option(26.5),
    center_lon: float = typer.Option(127.9),
    zoom: float = typer.Option(6.0),
    opacity: float = typer.Option(0.7),
    map_style: str = typer.Option("open-street-map"),
    write_html: bool = typer.Option(True),
    write_png: bool = typer.Option(False),
):

    output_dir = output_dir / input_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_parquet(input_path).to_crs("EPSG:4326")

    geojson = json.loads(gdf.to_json())

    for feature in geojson["features"]:
        feature["id"] = str(feature["properties"][id_col])

    target_cols = [c.strip() for c in columns.split(",")]

    for col in target_cols:
        if col not in gdf.columns:
            print(f"Skip missing column: {col}")
            continue

        fig = px.choropleth_map(
            gdf,
            geojson=geojson,
            locations=gdf[id_col].astype(str),
            color=col,
            hover_name=id_col,
            map_style=map_style,
            center={"lat": center_lat, "lon": center_lon},
            zoom=zoom,
            opacity=opacity,
            color_continuous_scale="Viridis",
        )

        fig.update_layout(
            title=col,
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
        )

        if write_html:
            html_path = output_dir / f"{col}.html"
            fig.write_html(html_path)
            print(f"Saved: {html_path}")

        if write_png:
            png_path = output_dir / f"{col}.png"
            fig.write_image(png_path, width=1200, height=900)
            print(f"Saved: {png_path}")


if __name__ == "__main__":
    app()
