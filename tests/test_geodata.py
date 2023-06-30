def test_import():
    import geodata


def test_planetery_items():
    import geodata

    Planetary = geodata.dems.Planetary(
        collection="3dep-lidar-dsm",
        bbox=[-121.846, 48.7, -121.823, 49],
        time_range="2000-12-01/2020-12-31",
    )

    Planetary.request_planetary_items()

    val = [
        "USGS_LPC_WA_Western_North_2016_LAS_2018-dsm-2m-5-16.tif",
        "USGS_LPC_WA_Western_North_2016_LAS_2018-dsm-2m-5-15.tif",
        "USGS_LPC_WA_Western_North_2016_LAS_2018-dsm-2m-4-16.tif",
        "USGS_LPC_WA_Western_North_2016_LAS_2018-dsm-2m-4-15.tif",
        "USGS_LPC_WA_MtBaker_2015_LAS_2017-dsm-2m-1-2.tif",
        "USGS_LPC_WA_MtBaker_2015_LAS_2017-dsm-2m-1-1.tif",
        "USGS_LPC_WA_MtBaker_2015_LAS_2017-dsm-2m-1-0.tif",
    ]

    for i in Planetary.dsm_file_names:
        if i not in val:
            print("expected:", i)

    assert Planetary.dsm_file_names == val
