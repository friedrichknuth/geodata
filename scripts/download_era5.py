import cdsapi
import numpy as np
from pathlib import Path
import warnings
import urllib3

warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)

c = cdsapi.Client()

output_file = 'data/scg_era5.nc'

xmin = -121.07246184
xmax = -121.04109889
ymax = 48.3720318
ymin = 48.34451837 

variables = ['2m_temperature', 
#              'snow_albedo', 
#              'snow_density',
             'snow_depth', 
#              'snow_depth_water_equivalent', 
#              'temperature_of_snow_layer',
             'total_precipitation',
        ]

years = [str(i) for i in np.arange(1950,2024,1)]
months = [str(i).zfill(2) for i in np.arange(1,13,1)]
days = [str(i).zfill(2) for i in np.arange(1,32,1)]
times = ['12:00',]


output_directory = Path(output_file).parent
output_directory.mkdir(exist_ok=True)
output_directory = output_directory.as_posix()

suffix = Path(output_file).suffix

for year in years:
    
    file_name = Path(output_file).with_suffix('').name
    out = Path(output_directory, file_name+'_'+str(year)+suffix).as_posix()
    print(out)



    c.retrieve(
        'reanalysis-era5-land',
        {
            'format': 'netcdf',
            'variable': variables,
            'year': [year,],
            'month': months,
            'day': days,
            'time': times,
            'area': [ymax, xmin, ymin, xmax],
        },out)
    
print('DONE')