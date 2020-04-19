# CoronaFramer
Easily generate U.S COVID-19 DataFrames with customizable census data

This software uses [COVID-19 data from the New York Times](https://github.com/nytimes/covid-19-data) and data collected from the 2018 American Community Survey
from the U.S Census. This allows for the easy creation of powerful data sets. This software can write CSV files for importation into statistical packages as well
as store the data in a pandas DataFrame for analysis within python

# Data Sources

**American Community Survey 2018 5-year estimates**

The American Community Survey is administered by the U.S Census Bureau. This survey contains information not normally on the per-decade Census such as internet access and other social factors. Learn more about it [here.](https://www.census.gov/programs-surveys/acs/about/acs-and-census.html)

**New York Times COVID-19 Github Repo**

The New York Times has been collecting data from state and local health departments since late Januarary 2020 and are used to create their COVID-19 maps. Learn more about it [here.](https://github.com/nytimes/covid-19-data)

***Google Community Mobility Report**

The Google Community Mobility report uses Google Maps data to categorized the relative change in baseline travel to certain types of locations such as businesses and parks. Learn more about it [here.](https://www.google.com/covid19/mobility/)

*Important Note: Locations that lack statistically significant amounts of data are entered as NaN on the data sets. Google recommends against using this data to compare trends between countries, or between settings such as rural vs urban.*

# Acknowledgements and License
This software uses COVID-19 data from the New York Times and demographic data from the 2018 American Community Survey. Addtionally, data from the Google Community Mobility Report is also used. The author of this software is eternally grateful
to all of these data sources for making this data free and open. This software also uses [pandas](https://github.com/pandas-dev/pandas) for DataFrame management and [CensusData](https://github.com/jtleider/censusdata) to connect to the U.S Census API. The author of this software would like to thank the maintainers of both of these projects for their valuable work.

This software is licensed under the GNU GPL v3 License. You are more than welcome to and encouraged to modify and distribute this software.
