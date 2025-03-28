from __future__ import annotations

from pathlib import Path

import fsspec
import numpy as np
import planetary_computer
import psutil
import pystac
import rioxarray
from pystac_client import Client


class Planetary:
    """
    A class to interact with Microsoft's Planetary Computer API for downloading
    Digital Surface Model (DSM) data from the 3DEP Lidar DSM collection.

    Parameters:
        base_url (str): The base URL for the Planetary Computer API.
        collection (str): The name of the data collection to query. Default is "3dep-lidar-dsm".
        bbox (list): The bounding box for the area of interest in [min_lon, min_lat, max_lon, max_lat] format.
        time_range (str): The time range for the data query in "YYYY-MM-DD/YYYY-MM-DD" format.
        output_folder (str): The folder where downloaded files will be saved.
        overwrite (bool): Whether to overwrite existing files in the output folder.

    Functions:
        request_items():
            Queries the Planetary Computer API for items matching the specified
            bounding box and time range. Stores the results and their filenames.

        download_3DEP_DSM():
            Downloads the DSM data for the queried items. Saves the data to the
            specified output folder. Handles file overwriting based on the
            `overwrite` attribute.

    Example:
        # Example usage of the Planetary class
        planetary = Planetary(
            bbox=[-121.846, 48.7, -121.823, 48.76],
            time_range="2000-12-01/2020-12-31",
            output_folder="downloads/Planetary",
            overwrite=False,
        )
        planetary.download_3DEP_DSM()
    """

    # TODO
    # - add support for returning virtual object as xarray dataset
    # - add support for writing vrt pointing to remote files
    # - add support for writing vrt pointing to local files

    def __init__(
        self,
        collection="3dep-lidar-dsm",
        bbox=[-121.846, 48.7, -121.823, 48.76],
        time_range="2000-12-01/2020-12-31",
        output_folder="downloads/Planetary",
        overwrite=bool(False),
    ):
        self.base_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
        self.collection = collection
        self.bbox = bbox
        self.time_range = time_range
        self.output_folder = output_folder
        self.overwrite = overwrite

    def request_items(self):
        print("bounding box:", self.bbox)
        print("time range:", self.time_range)

        Path(self.output_folder).mkdir(parents=True, exist_ok=True)

        catalog = Client.open(self.base_url)
        search = catalog.search(
            collections=[self.collection], bbox=self.bbox, datetime=self.time_range
        )
        items = search.item_collection()

        self.items = items

        dsm_file_names = []

        for i in self.items:
            url = i.assets["data"].href
            dsm_file_names.append(url.split("/")[-1])

        self.dsm_file_names = dsm_file_names

        print(len(self.items), "items found at", self.base_url)

    def download_3DEP_DSM(self):
        Planetary.request_items(self)

        exist = []
        payload = []
        for fn in self.dsm_file_names:
            out = Path(self.output_folder, fn)

            if out.exists() and not self.overwrite:
                exist.append(out)
            else:
                payload.append(out)
        if exist:
            print("overwrite set to False")
            print("the following files already exist:")
            for fn in exist:
                print(fn)

        if payload:
            print("downloading:")
            for fn in payload:
                print(fn)

            for fn in payload:
                item = pystac.Item.from_file(
                    "/".join(
                        [
                            self.base_url,
                            "collections",
                            self.collection,
                            "items",
                            fn.with_suffix("").name,
                        ]
                    )
                )

                signed_item = planetary_computer.sign(item)
                signed_item_url = signed_item.assets["data"].href

                ds = rioxarray.open_rasterio(signed_item_url)

                ds.rio.to_raster(fn, compress="lzw")

            print("download complete")

        elif not exist and not payload:
            print("no data available within specified bounds")
            print("check your bbox and time range inputs")


class Copernicus:
    def __init__(
        self,
        collection="copernicus-dem-90m",
        # bbox=[-121.846, 48.7, -121.823, 48.76], # easton
        bbox=[-24.23, 63.28, -13.33, 66.46],  # icealand
        output_folder="downloads/Copernicus",
        overwrite=bool(False),
    ):
        # TODO
        # - add test for valid bbox in different hemispheres
        # - add support for returning virtual object as xarray dataset
        # - add support for writing vrt pointing to remote files
        # - add support for writing vrt pointing to local files

        VALID_COLLECTIONS = {"copernicus-dem-90m", "copernicus-dem-30m"}

        if collection not in VALID_COLLECTIONS:
            raise ValueError(
                f"Invalid collection '{collection}'. Must be one of: {', '.join(VALID_COLLECTIONS)}"
            )

        self.base_url_s3 = f"s3://{collection}/"
        self.base_url_http = f"http://{collection}.s3.amazonaws.com/"
        self.bbox = bbox
        self.output_folder = output_folder
        self.overwrite = overwrite
        self.arcsecond = "3" if collection == "copernicus-dem-90m" else "1"
        self.fs = fsspec.filesystem("s3", anon=True)

    def build_urls(self):
        self.s3_urls = []
        self.http_urls = []
        xmin, ymin, xmax, ymax = self.bbox
        xmin, ymin, xmax, ymax = (
            int(np.floor(xmin)),
            int(np.floor(ymin)),
            int(np.ceil(xmax)),
            int(np.ceil(ymax)),
        )
        lons = np.arange(xmin, xmax + 1, 1)
        lats = np.arange(ymin, ymax + 1, 1)
        lons_str = []
        lats_str = []
        for lon in lons:
            if lon < 0:
                lons_str.append("W" + str(abs(lon)).zfill(3))
            else:
                lons_str.append("E" + str(abs(lon)).zfill(3))
        for lat in lats:
            if lat < 0:
                lats_str.append("S" + str(abs(lat)))
            else:
                lats_str.append("N" + str(abs(lat)))

        missing_tiles = []
        for lon in lons_str:
            for lat in lats_str:
                base_folder = (
                    "Copernicus_DSM_COG_"
                    + self.arcsecond
                    + "0_"
                    + lat
                    + "_00_"
                    + lon
                    + "_00_DEM/"
                )
                dem_file = (
                    "Copernicus_DSM_COG_"
                    + self.arcsecond
                    + "0_"
                    + lat
                    + "_00_"
                    + lon
                    + "_00_DEM.tif"
                )
                try:
                    s3_url = self.base_url_s3 + base_folder + dem_file
                    self.fs.open(s3_url, "rb")
                    self.s3_urls.append(s3_url)
                    http_url = self.base_url_http + base_folder + dem_file
                    self.http_urls.append(http_url)
                except:
                    missing_tiles.append(s3_url)
                    pass

        if self.s3_urls:
            print(len(self.s3_urls), "valid urls found")
        else:
            print("no valid urls found")
            if missing_tiles:
                print("Check validity of urls searched:")
                for tile in missing_tiles:
                    print(tile)

    def download_tiles(self):
        Copernicus.build_urls(self)
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)

        output_files = []
        for url in self.s3_urls:
            fn = Path(self.output_folder.rstrip("/") + "/", Path(url).name)
            # fn = Path(url.replace(self.base_url_s3, self.output_folder.rstrip('/')+'/'))
            output_files.append(fn)

        for i, url in enumerate(self.s3_urls):
            fn = output_files[i]
            ds = rioxarray.open_rasterio(self.fs.open(url, "rb"))
            ds.rio.to_raster(fn, compress="lzw")

        print("download complete")
