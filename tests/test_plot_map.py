from typing import cast

import geopandas as gpd
import plotly.graph_objects as go
from shapely.geometry import box
from src.plot_map import build_toggle_map, write_separate_maps


def test_build_toggle_map_uses_one_trace_and_updates_each_metric() -> None:
    gdf = gpd.GeoDataFrame(
        {
            "unit_id": ["a", "b"],
            "observation_count": [10, 20],
            "shannon_entropy": [1.25, 2.5],
        },
        geometry=[box(127, 26, 127.1, 26.1), box(127.1, 26, 127.2, 26.1)],
        crs="EPSG:4326",
    )
    geojson = gdf.__geo_interface__
    for feature, unit_id in zip(geojson["features"], gdf["unit_id"], strict=True):
        feature["id"] = unit_id

    fig = build_toggle_map(
        gdf,
        geojson,
        "unit_id",
        ["observation_count", "shannon_entropy"],
    )

    traces = cast(tuple[go.Choroplethmap, ...], fig.data)
    assert len(traces) == 1
    assert traces[0].type == "choroplethmap"
    assert list(cast(tuple[int, ...], traces[0].z)) == [10, 20]
    assert fig.layout.uirevision == "diversity-indices-map"

    buttons = fig.layout.updatemenus[0].buttons
    assert len(buttons) == 2
    assert [button.label for button in buttons] == ["観測数", "Shannon"]

    integer_update, integer_layout = buttons[0].args
    assert integer_update["z"] == [[10, 20]]
    assert integer_update["name"] == ["観測レコード数"]
    assert integer_update["colorbar.title.text"] == ["観測レコード数"]
    assert "%{z:,.0f}" in integer_update["hovertemplate"][0]
    assert integer_update["zauto"] == [True]
    assert integer_layout["title.text"] == "観測レコード数"

    decimal_update, decimal_layout = buttons[1].args
    assert decimal_update["z"] == [[1.25, 2.5]]
    assert decimal_update["name"] == ["Shannon entropy"]
    assert decimal_update["colorbar.title.text"] == ["Shannon entropy"]
    assert "%{z:.2f}" in decimal_update["hovertemplate"][0]
    assert decimal_update["zauto"] == [True]
    assert decimal_layout["title.text"] == "Shannon entropy"


def test_write_separate_maps_keeps_per_metric_png_output(monkeypatch, tmp_path) -> None:
    gdf = gpd.GeoDataFrame(
        {"unit_id": ["a"], "observation_count": [10], "species_richness": [3]},
        geometry=[box(127, 26, 127.1, 26.1)],
        crs="EPSG:4326",
    )
    written_paths = []
    monkeypatch.setattr(
        "plotly.graph_objects.Figure.write_image",
        lambda self, path, **kwargs: written_paths.append(path),
    )

    write_separate_maps(
        gdf,
        gdf.__geo_interface__,
        tmp_path,
        "unit_id",
        ["observation_count", "species_richness"],
        26.5,
        127.9,
        6,
        0.7,
        "open-street-map",
        write_png=True,
    )

    assert written_paths == [
        tmp_path / "observation_count.png",
        tmp_path / "species_richness.png",
    ]
