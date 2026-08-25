import json
from pathlib import Path
from typing import Annotated, Any

import geopandas as gpd
import plotly.graph_objects as go
import typer

app = typer.Typer()

DEFAULT_COLUMNS = "observation_count,species_richness,shannon_entropy,pielou_evenness,hill_q1_0,hill_q2_0"

METRIC_DISPLAY = {
    "observation_count": {"button": "観測数", "display": "観測レコード数"},
    "species_richness": {"button": "種数", "display": "種数"},
    "shannon_entropy": {"button": "Shannon", "display": "Shannon entropy"},
    "pielou_evenness": {"button": "Pielou", "display": "Pielou evenness"},
    "hill_q1_0": {"button": "Hill q=1", "display": "Hill number (q=1)"},
    "hill_q2_0": {"button": "Hill q=2", "display": "Hill number (q=2)"},
}

INTEGER_METRICS = {"observation_count", "species_richness"}
DEFAULT_OUTPUT_DIR = Path("outputs/maps")

REGIONAL_MAPS = {
    "map": {
        "label": "沖縄本島",
        "domain": {"x": [0.00, 0.58], "y": [0.05, 0.95]},
        "center": {"lat": 26.95, "lon": 127.55},
        "zoom": 7.7,
    },
    "map2": {
        "label": "八重山",
        "domain": {"x": [0.60, 0.94], "y": [0.53, 0.95]},
        "center": {"lat": 24.75, "lon": 123.80},
        "zoom": 6.8,
    },
    "map3": {
        "label": "宮古",
        "domain": {"x": [0.60, 0.76], "y": [0.05, 0.48]},
        "center": {"lat": 24.80, "lon": 125.10},
        "zoom": 7.6,
    },
    "map4": {
        "label": "大東",
        "domain": {"x": [0.78, 0.94], "y": [0.05, 0.48]},
        "center": {"lat": 25.20, "lon": 131.25},
        "zoom": 7.3,
    },
}


def _metric_settings(column: str) -> dict[str, str]:
    """Return labels and hover formatting for a metric column."""
    configured = METRIC_DISPLAY.get(column, {})
    return {
        "button": configured.get("button", column),
        "display": configured.get("display", column),
        "format": ",.0f" if column in INTEGER_METRICS else ".2f",
    }


def _hovertemplate(id_col: str, display_name: str, value_format: str) -> str:
    return f"{id_col}: %{{location}}<br>{display_name}: %{{z:{value_format}}}<extra></extra>"


def build_toggle_map(
    gdf: gpd.GeoDataFrame,
    geojson: dict[str, Any],
    id_col: str,
    columns: list[str],
    center_lat: float = 26.5,
    center_lon: float = 127.9,
    zoom: float = 6,
    opacity: float = 0.7,
    map_style: str = "open-street-map",
) -> go.Figure:
    """Build one choropleth whose metric is changed by horizontal buttons."""
    if not columns:
        raise ValueError("No valid metric columns are available to plot.")

    initial_column = columns[0]
    initial = _metric_settings(initial_column)
    locations = gdf[id_col].astype(str).tolist()

    trace = go.Choroplethmap(
        geojson=geojson,
        locations=locations,
        z=gdf[initial_column].tolist(),
        name=initial["display"],
        colorscale="Viridis",
        colorbar={"title": {"text": initial["display"]}},
        hovertemplate=_hovertemplate(id_col, initial["display"], initial["format"]),
        marker={"opacity": opacity},
        zauto=True,
    )

    buttons = []
    for column in columns:
        settings = _metric_settings(column)
        buttons.append(
            {
                "label": settings["button"],
                "method": "update",
                "args": [
                    {
                        "z": [gdf[column].tolist()],
                        "name": [settings["display"]],
                        "hovertemplate": [_hovertemplate(id_col, settings["display"], settings["format"])],
                        "colorbar.title.text": [settings["display"]],
                        "zauto": [True],
                    },
                    {"title.text": settings["display"]},
                ],
            }
        )

    fig = go.Figure(trace)
    fig.update_layout(
        title={"text": initial["display"]},
        map={
            "style": map_style,
            "center": {"lat": center_lat, "lon": center_lon},
            "zoom": zoom,
        },
        margin={"r": 0, "t": 100, "l": 0, "b": 0},
        updatemenus=[
            {
                "type": "buttons",
                "direction": "right",
                "x": 0,
                "xanchor": "left",
                "y": 1.08,
                "yanchor": "top",
                "showactive": True,
                "buttons": buttons,
            }
        ],
        uirevision="diversity-indices-map",
    )
    return fig


def build_regional_png_figure(
    gdf: gpd.GeoDataFrame,
    geojson: dict[str, Any],
    id_col: str,
    column: str,
    opacity: float = 0.85,
    map_style: str = "carto-positron",
) -> go.Figure:
    """Build a static four-panel regional map with one shared color scale."""
    settings = _metric_settings(column)
    values = gdf[column].tolist()
    finite_values = [float(value) for value in values if value is not None and value == value]
    if not finite_values:
        raise ValueError(f"Metric column '{column}' has no values to plot.")

    color_min = min(finite_values)
    color_max = max(finite_values)
    if color_min == color_max:
        color_min -= 0.5
        color_max += 0.5

    locations = gdf[id_col].astype(str).tolist()
    fig = go.Figure()
    for subplot_name in REGIONAL_MAPS:
        fig.add_trace(
            go.Choroplethmap(
                geojson=geojson,
                locations=locations,
                z=values,
                subplot=subplot_name,
                coloraxis="coloraxis",
                marker={
                    "opacity": opacity,
                    "line": {"color": "rgba(255,255,255,0.85)", "width": 0.6},
                },
                hoverinfo="skip",
                name=settings["display"],
            )
        )

    map_layouts = {
        subplot_name: {
            "style": map_style,
            "domain": config["domain"],
            "center": config["center"],
            "zoom": config["zoom"],
        }
        for subplot_name, config in REGIONAL_MAPS.items()
    }
    annotations = [
        {
            "text": config["label"],
            "x": sum(config["domain"]["x"]) / 2,
            "y": config["domain"]["y"][1] + 0.005,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "center",
            "yanchor": "bottom",
            "showarrow": False,
            "font": {"size": 19, "color": "#222"},
        }
        for config in REGIONAL_MAPS.values()
    ]

    layout_updates: dict[str, Any] = {
        **map_layouts,
        "coloraxis": {
            "colorscale": "Viridis",
            "cmin": color_min,
            "cmax": color_max,
            "colorbar": {
                "title": {"text": settings["display"], "side": "right"},
                "x": 0.965,
                "y": 0.5,
                "len": 0.88,
                "thickness": 24,
            },
        },
        "title": {
            "text": settings["display"],
            "x": 0.47,
            "xanchor": "center",
            "y": 0.995,
            "yanchor": "top",
            "font": {"size": 28},
        },
        "annotations": annotations,
        "margin": {"r": 55, "t": 75, "l": 10, "b": 10},
        "showlegend": False,
    }
    fig.update_layout(layout_updates)
    return fig


def write_separate_maps(
    gdf: gpd.GeoDataFrame,
    geojson: dict[str, Any],
    output_dir: Path,
    id_col: str,
    columns: list[str],
    center_lat: float,
    center_lon: float,
    zoom: float,
    opacity: float,
    map_style: str,
    write_html: bool = False,
    write_png: bool = False,
) -> None:
    """Write legacy per-metric HTML and/or regional static PNG maps."""
    for column in columns:
        if write_html:
            fig = build_toggle_map(
                gdf=gdf,
                geojson=geojson,
                id_col=id_col,
                columns=[column],
                center_lat=center_lat,
                center_lon=center_lon,
                zoom=zoom,
                opacity=opacity,
                map_style=map_style,
            )
            fig.update_layout(updatemenus=[])
            html_path = output_dir / f"{column}.html"
            fig.write_html(html_path)
            print(f"Saved: {html_path}")

        if write_png:
            fig = build_regional_png_figure(
                gdf=gdf,
                geojson=geojson,
                id_col=id_col,
                column=column,
            )
            png_path = output_dir / f"{column}_regions.png"
            fig.write_image(png_path, width=1800, height=1200)
            print(f"Saved: {png_path}")


def _valid_columns(gdf: gpd.GeoDataFrame, requested: list[str]) -> list[str]:
    valid = []
    for column in requested:
        if column not in gdf.columns:
            print(f"Skip missing column: {column}")
            continue
        valid.append(column)

    if not valid:
        raise typer.BadParameter(
            "None of the requested metric columns exist in the input data.",
            param_hint="--columns",
        )
    return valid


@app.command()
def main(
    input_path: Path,
    output_dir: Annotated[Path, typer.Option()] = DEFAULT_OUTPUT_DIR,
    id_col: Annotated[str, typer.Option()] = "unit_id",
    columns: Annotated[str, typer.Option()] = DEFAULT_COLUMNS,
    center_lat: Annotated[float, typer.Option()] = 26.5,
    center_lon: Annotated[float, typer.Option()] = 127.9,
    zoom: Annotated[float, typer.Option()] = 6,
    opacity: Annotated[float, typer.Option()] = 0.7,
    map_style: Annotated[str, typer.Option()] = "open-street-map",
    write_html: Annotated[bool, typer.Option()] = True,
    write_png: Annotated[bool, typer.Option()] = False,
    write_separate_html: Annotated[bool, typer.Option()] = False,
) -> None:
    output_dir = output_dir / input_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_parquet(input_path).to_crs("EPSG:4326")
    if id_col not in gdf.columns:
        raise typer.BadParameter(
            f"ID column '{id_col}' does not exist in the input data.",
            param_hint="--id-col",
        )

    geojson = json.loads(gdf.to_json())
    for feature in geojson["features"]:
        feature["id"] = str(feature["properties"][id_col])

    requested_columns = [column.strip() for column in columns.split(",") if column.strip()]
    valid_columns = _valid_columns(gdf, requested_columns)

    if write_html:
        fig = build_toggle_map(
            gdf=gdf,
            geojson=geojson,
            id_col=id_col,
            columns=valid_columns,
            center_lat=center_lat,
            center_lon=center_lon,
            zoom=zoom,
            opacity=opacity,
            map_style=map_style,
        )
        html_path = output_dir / "diversity_indices.html"
        fig.write_html(html_path)
        print(f"Saved: {html_path}")

    if write_separate_html or write_png:
        write_separate_maps(
            gdf=gdf,
            geojson=geojson,
            output_dir=output_dir,
            id_col=id_col,
            columns=valid_columns,
            center_lat=center_lat,
            center_lon=center_lon,
            zoom=zoom,
            opacity=opacity,
            map_style=map_style,
            write_html=write_separate_html,
            write_png=write_png,
        )


if __name__ == "__main__":
    app()
