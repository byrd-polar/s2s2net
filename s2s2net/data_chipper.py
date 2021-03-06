# %%
import glob
import os

import geopandas as gpd
import numpy as np
import pandas as pd
import rioxarray
import tqdm

# %%
# Create subdirectories to put the data in
# os.makedirs("SuperResolution/chips/geotiff/image", exist_ok=True)
# os.makedirs("SuperResolution/chips/geotiff/mask", exist_ok=True)
os.makedirs("SuperResolution/chips/npy/image", exist_ok=True)
os.makedirs("SuperResolution/chips/npy/mask", exist_ok=True)
os.makedirs("SuperResolution/chips/npy/hres", exist_ok=True)

# %%
# Reserve specific tiles as a test set, and the rest are for training/validation
tile_gdf: gpd.GeoDataFrame = gpd.read_file(
    filename="SuperResolution/s2s2net_training_tiles.geojson"
)
test_tile_ids = ["0123", "0124", "0125", "0126", "0211", "0223", "0157", "0439"]
train_tile_gdf = tile_gdf.query(expr="folder_id not in @test_tile_ids")

# %%
# Main loop to create the image chips that will become the training dataset
j: int = 0
for _, row in tqdm.tqdm(iterable=train_tile_gdf.iterrows(), total=len(train_tile_gdf)):
    with (
        rioxarray.open_rasterio(filename=row.sen2_file) as ds_sen2,
        rioxarray.open_rasterio(filename=row.mask_file) as ds_mask,
        rioxarray.open_rasterio(filename=row.hres_file) as ds_hres,
    ):
        for x in range(int(ds_sen2.x.min()), int(ds_sen2.x.max()) - 5120, 5120):
            for y in range(int(ds_sen2.y.min()), int(ds_sen2.y.max()) - 5120, 5120):

                crop_ds_sen2 = ds_sen2.rio.clip_box(
                    minx=x, miny=y, maxx=x + 5120 - 10, maxy=y + 5120 - 10
                )
                if crop_ds_sen2.shape == (6, 512, 512):  # full size tiles only
                    crop_ds_mask = ds_mask.rio.clip_box(
                        minx=x, miny=y, maxx=x + 5120 - 2.5, maxy=y + 5120 - 2.5
                    )
                    assert crop_ds_mask.shape == (1, 2560, 2560)

                    crop_ds_hres = ds_hres.rio.clip_box(
                        minx=x, miny=y, maxx=x + 5120 - 2.5, maxy=y + 5120 - 2.5
                    )
                    assert crop_ds_hres.shape == (4, 2560, 2560)

                    # Don't save chips with NaN or 0 only values
                    if (
                        # Don't save chips with NaN values
                        np.isnan(crop_ds_sen2.data.min())
                        or np.isnan(crop_ds_mask.data.min())
                        # Don't save chips with 0 only values
                        # or crop_ds_sen2.max() == 0
                        # or crop_ds_mask.max() == 0
                    ):
                        continue
                    # assert crop_ds_hres.max() != 0

                    # Save as npy file format
                    np.save(
                        file=f"SuperResolution/chips/npy/image/SEN2_{j:04d}.npy",
                        arr=crop_ds_sen2,
                    )
                    np.save(
                        file=f"SuperResolution/chips/npy/mask/MASK_{j:04d}.npy",
                        arr=crop_ds_mask,
                    )
                    np.save(
                        file=f"SuperResolution/chips/npy/hres/HRES_{j:04d}.npy",
                        arr=crop_ds_hres,
                    )

                    # Save as geotiff file format
                    # crop_ds_sen2.rio.to_raster(
                    #     raster_path=f"SuperResolution/chips/geotiff/image/SEN2_{j:04d}.tif"
                    # )
                    # crop_ds_mask.rio.to_raster(
                    #     raster_path=f"SuperResolution/chips/geotiff/mask/MASK_{j:04d}.tif"
                    # )
                    # crop_ds_mask.rio.to_raster(
                    #     raster_path=f"SuperResolution/chips/geotiff/hres/HRES_{j:04d}.tif"
                    # )

                    j += 1
