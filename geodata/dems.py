from __future__ import annotations

from pathlib import Path
import pystac
from pystac_client import Client
import planetary_computer
import rioxarray
import psutil


class Planetary:
    def __init__(
        self,
        collection="3dep-lidar-dsm",
        bbox=[-121.846, 48.7, -121.823, 48.76],
        time_range="2000-12-01/2020-12-31",
        output_folder="downloads",
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
            print("\noverwrite set to False")
            print("\nthe following files already exist:")
            for fn in exist:
                print(fn)

        if payload:
            print("\ndownloading:")
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

                ds.rio.to_raster(out, compress="lzw")

            print("\ndownload complete")

        elif not exist and not payload:
            print("\nno data available within specified bounds")
            print("check your bbox and time range inputs")
