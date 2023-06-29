import click

import dataquery


@click.command()
@click.option(
    "--collection",
    prompt=True,
    default="3dep-lidar-dsm",
    help="Plantery Computer collection name. Default: 3dep-lidar-dsm",
)
@click.option(
    "--bbox",
    prompt=True,
    default="-121.846 48.7 -121.823 48.76",
    help="xmin, ymin, xmax, ymax. Default: '-121.846 48.7 -121.823 48.76'",
)
@click.option(
    "--time-range",
    prompt=True,
    default="2000-12-01/2020-12-31",
    help="Time range. Default: 2000-12-01/2020-12-31",
)
@click.option(
    "--output-folder",
    prompt=True,
    default="downloads",
    help="Output folder. Default: downloads",
)
@click.option("--overwrite", default=False, help="Set to overwrite existing outputs")
def main(
    collection,
    bbox,
    time_range,
    output_folder,
    overwrite,
):
    bbox = [float(x) for x in bbox.split(" ")]

    dataquery.dems.download_planetary_3DEP_DSM(
        collection,
        bbox,
        time_range,
        output_folder,
        overwrite,
    )


if __name__ == "__main__":
    main()
