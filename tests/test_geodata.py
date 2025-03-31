import geodata


class TestPlanetary:
    def test_planetary_request_items(self):
        """Test the Planetary class's request_items method."""
        planetary = geodata.dems.Planetary(
            collection="3dep-lidar-dsm",
            bbox=[-121.846, 48.7, -121.823, 49],
            time_range="2000-12-01/2020-12-31",
        )

        planetary.request_items()

        expected_files = [
            "USGS_LPC_WA_Western_North_2016_LAS_2018-dsm-2m-5-16.tif",
            "USGS_LPC_WA_Western_North_2016_LAS_2018-dsm-2m-5-15.tif",
            "USGS_LPC_WA_Western_North_2016_LAS_2018-dsm-2m-4-16.tif",
            "USGS_LPC_WA_Western_North_2016_LAS_2018-dsm-2m-4-15.tif",
            "USGS_LPC_WA_MtBaker_2015_LAS_2017-dsm-2m-1-2.tif",
            "USGS_LPC_WA_MtBaker_2015_LAS_2017-dsm-2m-1-1.tif",
            "USGS_LPC_WA_MtBaker_2015_LAS_2017-dsm-2m-1-0.tif",
        ]

        assert planetary.dsm_file_names == expected_files


class TestCopernicus:
    def setup_method(self):
        """Setup method to initialize test data."""
        self.bbox_list = [
            [-121.846, 48.700, -121.823, 48.760],  # NW Hemisphere
            [8.020, 46.380, 8.120, 46.450],  # NE Hemisphere
            [-73.620, -48.418, -73.520, -48.350],  # SW Hemisphere
            [73.470, -53.120, 73.550, -53.050],  # SE Hemisphere
        ]

        self.expected_urls = [
            [
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_N48_00_W122_00_DEM/Copernicus_DSM_COG_30_N48_00_W122_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_N49_00_W122_00_DEM/Copernicus_DSM_COG_30_N49_00_W122_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_N48_00_W121_00_DEM/Copernicus_DSM_COG_30_N48_00_W121_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_N49_00_W121_00_DEM/Copernicus_DSM_COG_30_N49_00_W121_00_DEM.tif",
            ],
            [
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_N46_00_E008_00_DEM/Copernicus_DSM_COG_30_N46_00_E008_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_N47_00_E008_00_DEM/Copernicus_DSM_COG_30_N47_00_E008_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_N46_00_E009_00_DEM/Copernicus_DSM_COG_30_N46_00_E009_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_N47_00_E009_00_DEM/Copernicus_DSM_COG_30_N47_00_E009_00_DEM.tif",
            ],
            [
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_S49_00_W074_00_DEM/Copernicus_DSM_COG_30_S49_00_W074_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_S48_00_W074_00_DEM/Copernicus_DSM_COG_30_S48_00_W074_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_S49_00_W073_00_DEM/Copernicus_DSM_COG_30_S49_00_W073_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_S48_00_W073_00_DEM/Copernicus_DSM_COG_30_S48_00_W073_00_DEM.tif",
            ],
            [
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_S54_00_E073_00_DEM/Copernicus_DSM_COG_30_S54_00_E073_00_DEM.tif",
                "s3://copernicus-dem-90m/Copernicus_DSM_COG_30_S53_00_E073_00_DEM/Copernicus_DSM_COG_30_S53_00_E073_00_DEM.tif",
            ],
        ]

    def test_copernicus_build_urls(self):
        """Test the Copernicus class's build_urls method."""
        for i, bbox in enumerate(self.bbox_list):
            copernicus = geodata.dems.Copernicus(bbox=bbox)
            copernicus.build_urls()
            assert copernicus.s3_urls == self.expected_urls[i]
