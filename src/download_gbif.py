from pathlib import Path
import time

import pandas as pd
import typer
from pygbif import occurrences
from tqdm import tqdm

app = typer.Typer()

DEFAULT_OUTPUT = Path("../data/raw/")


def fetch_gbif_plants(
    country: str,
    state_province: str,
    start_year: int,
    end_year: int,
    limit_per_request: int,
    max_records: int,
    offset_start: int,
):
    all_results = []
    init_offset = 0
    final_offset = init_offset + limit_per_request * (max_records//limit_per_request)
    for offset in tqdm(range(offset_start,
                             final_offset,
                             limit_per_request)):
        res = occurrences.search(
            country=country,
            stateProvince=state_province,
            kingdomKey=6,  # Plantae
            hasCoordinate=True,
            year=f"{start_year},{end_year}",
            limit=limit_per_request,
            offset=offset
        )

        results = res["results"]
        all_results.extend(results)

        time.sleep(0.2)  # 念のため軽く待つ
        
    return pd.DataFrame(all_results[:max_records])


@app.command()
def main(
    country: str = typer.Option(
        "JP",
        help="Country code",
    ),
    state_province: str = typer.Option(
        "Okinawa",
        help="State or prefecture name",
    ),
    start_year: int = typer.Option(
        2015,
        help="Start year",
    ),
    end_year: int = typer.Option(
        2026,
        help="End year",
    ),
    limit_per_request: int = typer.Option(
        300,
        help="GBIF API page size",
    ),
    max_records: int = typer.Option(
        3000,
        help="Maximum number of records to fetch",
    ),
    offset_start: int = typer.Option(
        0,
        help="Initial GBIF offset",
    ),
    output_dir: Path = typer.Option(
        DEFAULT_OUTPUT,
        help="Output parquet path",
    ),
):
    """
    Download GBIF plant occurrence data
    and save as parquet.
    """

    output_dir.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching GBIF data...")

    df = fetch_gbif_plants(
        country=country,
        state_province=state_province,
        start_year=start_year,
        end_year=end_year,
        limit_per_request=limit_per_request,
        max_records=max_records,
        offset_start=offset_start,
    )




    output_dir = Path("../data/raw")
    fname = f"gbif_{state_province}-{country}_plants_{start_year}-{end_year}-{max_records}.parquet"

    df.to_parquet(
        output_dir / fname,
        index=False
    )

    print(f"Final dataframe shape: {df.shape}")

    print(f"Saved parquet to: {output_dir/fname}")


if __name__ == "__main__":
    app()
