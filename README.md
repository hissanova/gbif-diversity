# GBIFデータを用いた沖縄県の植物多様性可視化

## 概要
本プロジェクトでは、GBIFから取得した沖縄県内の植物出現データを用いて、植物多様性の空間パターンを可視化します。

観測点データを市町村境界またはグリッドに割り当て、以下の指標を計算します。

- 観測数
- 種数（species richness）
- Shannon entropy
- Pielou's evenness
- Hill number
- 植物相クラスタリング

単なる観測点の地図化ではなく、種数・均等性・実効種数・群集構成の違いを比較することで、地域ごとの植物多様性の見え方を探索することを目的としています。

## 目的

- GBIFの植物出現データを取得し、再利用可能な形で保存する
- 市町村単位またはグリッド単位で植物多様性指標を計算する
- 多様性指標ごとの空間パターンの違いを可視化する
- 植物種構成に基づいて地域をクラスタリングする
- 将来的に、植生・環境要因・生態系安定性の関係を分析するための基盤を作る

## 使用データ

- GBIF occurrence data
- 沖縄県市町村境界データ

GBIFの出現データには観測努力の偏りが含まれるため、本プロジェクトの結果は「真の植物分布」ではなく、GBIFに記録された観測データに基づく多様性パターンとして解釈します。

## 使用技術

- Python
- pandas
- GeoPandas
- Plotly
- PyGBIF
- Typer
- Parquet
- SciPy

## ディレクトリ構成

```text
gbif-okinawa-plant-diversity/
├── data/
│   ├── raw/
│   ├── processed/
│   └── boundary/
├── outputs/
│   └── maps/
├── notebooks/
├── src/
│   ├── download_gbif.py
│   ├── preprocess.py
│   ├── compute_indices.py
│   ├── compute_clusters.py
│   └── plot_maps.py
├── README.md
└── pyproject.toml
```

## 実行例
1. GBIF取得
```shell
python src/download_gbif.py \
  --start-year 2015 \
  --end-year 2026 \
  --max-records 30000 \
  --output data/raw/gbif_okinawa_plants.parquet
```
2. 前処理
```shell
python src/preprocess.py \
  --input-path data/raw/gbif_okinawa_plants.parquet \
  --output-path data/processed/gbif_okinawa_plants_cleaned.parquet
```
3. 5kmグリッドで指標計算
```shell
python src/compute_indices.py \
  --mode grid \
  --grid-size-m 5000 \
  --q-values 0,1,2 \
  --output-path data/processed/grid_5km_diversity.parquet
```
4. 市町村単位で指標計算
```shell
python src/compute_indices.py \
  --mode municipality \
  --municipality-col N03_004 \
  --output-path data/processed/municipality_diversity.parquet
```
5. 地図出力
```shell
python src/plot_maps.py \
  --input-path data/processed/grid_5km_diversity.parquet \
  --output-dir outputs/maps/grid_5km \
  --columns observation_count,species_richness,shannon_entropy,pielou_evenness,hill_q1_0,hill_q2_0
```
PNGも出す場合：
```shell
python src/plot_maps.py \
  --input-path data/processed/grid_5km_diversity.parquet \
  --output-dir outputs/maps/grid_5km \
  --write-png
```
