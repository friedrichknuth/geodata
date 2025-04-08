from __future__ import annotations

import subprocess
from pathlib import Path

import fsspec
import numpy as np
import planetary_computer
import psutil
import pystac
import rioxarray
import stackstac
import xarray as xr
from pystac_client import Client

# TODO
# - create a general class to handle common operations between Copernicus and Planetary classes
#   - returning virtual object as xarray dataset
#   - add support for writing vrt pointing to remote files
#   - add support for writing vrt pointing to local files


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
        collection: str = "3dep-lidar-dsm",
        bbox: list[float] = [-121.846, 48.7, -121.823, 48.76],
        time_range: str = "2000-12-01/2020-12-31",
        output_folder: str = "downloads/Planetary",
        overwrite: bool = False,
    ):
        """
        Initialize the Planetary class.

        Parameters:
            collection (str): The name of the data collection to query. Default is "3dep-lidar-dsm".
            bbox (list[float]): The bounding box for the area of interest in [min_lon, min_lat, max_lon, max_lat] format.
            time_range (str): The time range for the data query in "YYYY-MM-DD/YYYY-MM-DD" format.
            output_folder (str): The folder where downloaded files will be saved.
            overwrite (bool): Whether to overwrite existing files in the output folder.
        """
        self.base_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
        self.collection = collection
        self.bbox = bbox
        self.time_range = time_range
        self.output_folder = Path(output_folder)
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
        collection: str = "copernicus-dem-90m",
        bbox: List[float] = [-24.23, 63.28, -13.33, 66.46],
        output_folder: str = "downloads/Copernicus",
        overwrite: bool = False,
    ):
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
        self.local_tiles = []

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
            print(
                len(self.s3_urls),
                "valid tile URLs found within the specified bounding box.",
            )
        else:
            error_message = "No valid tile URLs found for the specified bounding box. "
            if missing_tiles:
                error_message += (
                    "The following tile URLs are missing or inaccessible:\n"
                )
                error_message += "\n".join(missing_tiles)
                raise ValueError(error_message)

    def download_tiles(self, overwrite=False):
        Copernicus.build_urls(self)
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)

        output_files = []
        for url in self.s3_urls:
            fn = Path(self.output_folder.rstrip("/") + "/", Path(url).name)
            output_files.append(fn)

        to_download = []
        for i, fn in enumerate(output_files):
            if fn.exists() and not overwrite:
                print(f"File {fn} already exists. Skipping download.")
            else:
                to_download.append((self.s3_urls[i], fn))

        if not to_download:
            print("No new tiles to download.")
            return

        for url, fn in to_download:
            da = rioxarray.open_rasterio(self.fs.open(url, "rb"))
            da.rio.to_raster(fn, compress="lzw")

        self.local_tiles = output_files

        print("Download complete")

    def lazy_load_tiles(self):
        Copernicus.build_urls(self)
        data = []
        for url in self.s3_urls:
            da = rioxarray.open_rasterio(self.fs.open(url, "rb"), chunks="auto")
            data.append(da)
        da = xr.combine_by_coords(data)
        return da

    def build_vrt_from_remote_tiles(
        self, output_folder=None, vrt_file_name="combined.vrt"
    ):
        Copernicus.build_urls(self)
        if output_folder is None:
            output_folder = self.output_folder
        output_file = Path(output_folder, vrt_file_name)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if self.overwrite:
            output_file.unlink(missing_ok=True)
        command = " ".join(["gdalbuildvrt", output_file.as_posix()] + self.http_urls)
        if output_file.exists():
            print(
                f"File {output_file} already exists and overwrite set to {self.overwrite}."
            )
            print("Skipping build.")
        else:
            print(f"Building VRT file: {output_file}")
            subprocess.run(command, shell=True, check=True)

    def build_vrt_from_local_tiles(
        self, local_tiles=None, output_folder=None, vrt_file_name="combined.vrt"
    ):
        if not local_tiles and not self.local_tiles:
            raise ValueError(
                "No local tiles found. Please specify local_tiles input or download tiles first."
            )
        elif not local_tiles and self.local_tiles:
            local_tiles = self.local_tiles
        local_tiles = [Path(tile).as_posix() for tile in local_tiles]
        if output_folder is None:
            output_folder = self.output_folder
        output_file = Path(output_folder, vrt_file_name)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if self.overwrite:
            output_file.unlink(missing_ok=True)
        command = " ".join(["gdalbuildvrt", output_file.as_posix()] + local_tiles)
        if output_file.exists():
            print(
                f"File {output_file} already exists and overwrite set to {self.overwrite}."
            )
            print("Skipping build.")
        else:
            print(f"Building VRT file: {output_file}")
            subprocess.run(command, shell=True, check=True)


class PGC:
    def __init__(
        self,
        collection: str = "arcticdem-mosaics-v3.0-32m",
        bbox: list[float] = [-19.4, 63.5, -18.8, 63.8],  # myrdalsjokull
        # bbox: list[float] = [-61.25390699 -65.32412875 -59.22577797 -64.82460726],# rema
        epsg_code: int = None,
        time_range: str = "2000-12-01/2025-12-31",
        output_folder: str = "downloads/PGC",
        overwrite: bool = False,
    ):
        # TODO
        # - add support for downloading mosaics
        # - add support for downloading strips
        # - create subclass for mosaics and strips
        # - add support for returning virtual strips object as xarray dataset
        # - add support for writing vrt pointing to remote files
        # - add support for writing vrt pointing to local files

        """
        Initialize the PGC class.

        Parameters:
            collection (str): The name of the data collection to query. Default is "3dep-lidar-dsm".
            bbox (list[float]): The bounding box for the area of interest in [min_lon, min_lat, max_lon, max_lat] format.
            epsg_code (int): The EPSG code for the desired output coordinate reference system. Default is None.
            time_range (str): The time range for the data query in "YYYY-MM-DD/YYYY-MM-DD" format.
            output_folder (str): The folder where downloaded files will be saved.
            overwrite (bool): Whether to overwrite existing files in the output folder.
        """
        self.base_url = "https://stac.pgc.umn.edu/api/v1/"
        self.collection = collection
        self.bbox = bbox
        self.epsg_code = epsg_code
        self.time_range = time_range
        self.output_folder = Path(output_folder)
        self.overwrite = overwrite

        VALID_COLLECTIONS = {
            "arcticdem-mosaics-v3.0-2m",
            "arcticdem-mosaics-v3.0-10m",
            "arcticdem-mosaics-v3.0-32m",
            "arcticdem-mosaics-v4.1-2m",
            "arcticdem-mosaics-v4.1-10m",
            "arcticdem-mosaics-v4.1-32m",
            "arcticdem-strips-s2s041-2m",
            "earthdem-strips-s2s041-2m",
            "rema-mosaics-v2.0-2m",
            "rema-mosaics-v2.0-10m",
            "rema-mosaics-v2.0-32m",
            "rema-strips-s2s041-2m",
        }
        if self.collection not in VALID_COLLECTIONS:
            raise ValueError(
                f"Invalid collection '{collection}'. Must be one of: {', '.join(VALID_COLLECTIONS)}"
            )
        catalog = Client.open(self.base_url)
        search = catalog.search(
            collections=[self.collection], bbox=self.bbox, datetime=self.time_range
        )
        items = search.item_collection()
        self.items = items

        if not self.epsg_code:
            self.epsg_code = int(self.items[0].properties["proj:code"].strip("EPSG:"))

    def get_stack(self):
        # TODO
        # - need to rethink this and likely have a seperate method for mosaics and strips
        #   that is only available based on the collection specified during initialization
        stack = stackstac.stack(
            self.items, epsg=self.epsg_code, bounds_latlon=self.bbox
        )
        stack = stack.mean(dim="time").squeeze()
        return stack


class ESA:
    def __init__(
        self,
        collection: str = "esa-worldcover",
        bbox: list[float] = [-19.4, 63.5, -18.8, 63.8],  # myrdalsjokull
        epsg_code: int = 4326,
        output_folder: str = "downloads/ESA",
    ):
        """
        Initialize the ESA class.

        """
        self.base_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
        self.collection = collection
        self.bbox = bbox
        self.epsg_code = epsg_code
        self.output_folder = Path(output_folder)

        catalog = Client.open(self.base_url, modifier=planetary_computer.sign_inplace)
        search = catalog.search(
            collections=[self.collection],
            bbox=self.bbox,
        )
        items = search.item_collection()

        self.items = items[1]  # add time option for mosaic selection

    def get_stack(self):
        stack = stackstac.stack(
            self.items, assets=["map"], epsg=self.epsg_code, bounds_latlon=self.bbox
        )
        categories = self.items.assets["map"].extra_fields["classification:classes"]
        return stack.squeeze(), categories
