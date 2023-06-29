from pathlib import Path
import pystac
from pystac_client import Client
import planetary_computer
import rioxarray
import psutil


def download_planetary_3DEP_DSM(
    collection="3dep-lidar-dsm",
    bbox=[-121.846, 48.7, -121.823, 48.76],
    time_range="2000-12-01/2020-12-31",
    output_folder="downloads",
    overwrite=False,
):
    base_url = "https://planetarycomputer.microsoft.com/api/stac/v1"

    print("bounding box:", bbox)
    print("time range:", time_range)

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    dsm_file_names = []
    catalog = Client.open(base_url)
    search = catalog.search(collections=[collection], bbox=bbox, datetime=time_range)
    items = search.item_collection()

    print(len(items), "items found at", base_url)
    for i in items:
        url = i.assets["data"].href
        dsm_file_names.append(url.split("/")[-1])

    exist = []
    payload = []
    for fn in dsm_file_names:
        out = Path(output_folder, fn)

        if out.exists() and not overwrite:
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
                        base_url,
                        "collections",
                        collection,
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

        return True

    elif not exist and not payload:
        print("\nno data available within specified bounds")
        print("check your bbox and time range inputs")

        return False
