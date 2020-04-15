import os
import datetime as dt
import logging
import argparse
from urllib import request
from datetime import datetime

import pandas as pd
import censusdata

nyt_path = os.getcwd() + '/nyt_data/'
output_data_path = os.getcwd() + '/output_data/'
log_path = os.getcwd() + '/logs/'

now = datetime.now()

# Built in variables that will likely be of common interest
interest_variables = ['B19326_001E', 'B01002_001E', 'B01001_001E', 'B08006_008E', 'B27001_001E', 'B28007_009E']
variable_name_map = {'B19326_001E': 'med_income', 'B01002_001E': 'age', 'B01001_001E': 'pop_size',
                     'B08006_008E': 'tot_public_transit_users', 'B27001_001E': 'tot_health_insurance',
                     'B28007_009E': 'tot_unemployed'}

if os.path.exists(log_path) is not True:
    os.mkdir(log_path)

log_format = '%(levelname)s | %(asctime)s | %(message)s'
logging.basicConfig(filename=log_path + 'coronaframer.log', format=log_format, filemode='w', level=logging.INFO)
logger = logging.getLogger()

arg_parser = argparse.ArgumentParser(
    description='Combine demographic data from the U.S Census with COVID-19 data',
    prog='CoronaFramer'
)

arg_parser.add_argument('-s', '--states', nargs='+', help='Specify the state or states to gather info on',
                        action='append')
arg_parser.add_argument('-c', '--counties', nargs='*', default='ALL',
                        help='Specify the counties to include. Default is all', action='append')
arg_parser.add_argument('-i', '--interactive', action='store_true',
                        help="Sets the program to run in interactive mode.")
arg_parser.add_argument('-sm', '--select_mode', nargs=1, default='positive', choices=['positive', 'negative'],
                        help='Selection mode for counties. Positive selects only the specified counties, negative '
                             'select chooses all counties in the state except for those counties. Default is positive.')
arg_parser.add_argument('-v', '--variables', nargs='*', default='DEFAULT',
                        help='Which census variables to select. Default is all default variables included with this '
                             'program')


def get_nyt_data(loc_type='counties', date_filter='now') -> pd.DataFrame:
    """
    Downloads COVID-19 data from the NYT Github
    :param: loc_type: The level of location data to get. Default is counties. Can be either states or counties
    :param: date_filter: What dates should be included? Valid inputs are "now", "all", and any valid date on or after
    01/21/2020. Dates should be entered as 'YYYY-MM-DD'
    :return: A DataFrame of the NYT COVID-19 Data
    """
    logger.info('Attemping to download NYT COVID-19 Data...')

    if loc_type != 'counties' and loc_type != 'states':
        raise ValueError('Location type must be either "counties", "states"!')

    if loc_type == 'counties':
        file_link = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
        file_name = 'nyt_data_county.csv'
    else:
        file_link = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'
        file_name = 'nyt_data_state.csv'

    if os.path.exists(nyt_path) is not True:
        os.mkdir(nyt_path)

    file_req = request.Request(file_link)
    csv_file = request.urlopen(file_req)
    csv_data = csv_file.read()

    with open(nyt_path + file_name, 'wb') as file:
        file.write(csv_data)

    nyt_data = pd.read_csv(nyt_path + file_name)

    if loc_type == 'counties':
        # Remove any unknown counties as census data cannot be retrieved for unknown places
        nyt_data.drop(nyt_data[nyt_data.county == 'Unknown'].index, inplace=True)

    if date_filter == 'all':
        logger.info('Finished Downloading NYT COVID-19 Data!')
        return nyt_data
    elif date_filter == 'now':
        logger.info('Finished Downloading NYT COVID-19 Data!')
        is_now = nyt_data['date'] == now.strftime('%Y-%m-%d')

        return nyt_data[is_now]
    else:
        logger.info('Finished Downloading NYT COVID-19 Data!')
        is_date = nyt_data['date'] == date_filter

        return nyt_data[is_date]


def get_fips_for_location(loc_type: str) -> [tuple]:
    """
    Gets a list of all the FIPS numbers for a given location
    :param loc_type: Either 'counties' or 'states'
    :return: A list of tuples containing (County, State, FIPS) if county level data or (State, FIPS) if state level
    """
    data = get_nyt_data(loc_type)

    if data.empty:
        yesterday = now - dt.timedelta(1)

        data = get_nyt_data(loc_type, yesterday.strftime('%Y-%m-%d'))

    if loc_type != 'counties' and loc_type != 'states':
        raise ValueError('Location type must be either "counties", "states"!')

    if loc_type == 'counties':
        ret_list = [(county, state, str(fips).replace('.0', '')) for county, state, fips in
                    zip(data['county'], data['state'], data['fips'])]
    else:
        ret_list = [(state, str(fips).replace('.0', '')) for state, fips in zip(data['state'], data['fips'])]

    return ret_list


def get_state_fips(state: str) -> str:
    """
    Gets the FIPS code for a state
    :param state: The state to get the FIPS code for
    :return: The FIPS code for the state
    """

    state_pairs = [pair[1] for pair in get_fips_for_location('states') if pair[0] == state]

    return state_pairs[0]


def build_frame_for_state(state: str, variables: list, save=True, rename_map={}) -> pd.DataFrame:
    """
    Builds a DataFrame with the requested variables
    :param rename_map: Dictionary used to rename variables. Optional
    :param save: Should the DataFrame be saved? Default is true
    :param variables: The Census variables to download
    :param state: The state of interest
    :return: A DataFrame of the joined NYT data and Census data
    """
    if os.path.exists(output_data_path) is not True:
        os.mkdir(output_data_path)

    county_data = [county_pair for county_pair in get_fips_for_location('counties') if county_pair[1] == state]
    state_fips = get_state_fips(state)
    state_covid_data = get_nyt_data('counties')
    value_dict = {}

    if state_covid_data.empty:
        yesterday = now - dt.timedelta(1)

        state_covid_data = get_nyt_data('counties', yesterday.strftime('%Y-%m-%d'))

    state_covid_data = state_covid_data[state_covid_data['state'] == state]

    for county in county_data:
        # The county FIPS is a 5 digit code. The first two digits refer to the state, the last three refer to the county
        county_fips = county[2][2:]

        if len(county[2]) == 4:
            county_fips = county[2][1:]
        if len(state_fips) == 1:
            state_fips = '0' + state_fips

        county_state = county[1]

        if state == county_state:
            logger.info(f'Attempting to download 2018 Census data for {county[0]} with FIPS {county_fips}')
            print(f'Attempting to download 2018 Census data for {county[0]} with FIPS {county_fips}')
            geo = censusdata.censusgeo([('state', state_fips), ('county', county_fips)])
            census_data = censusdata.download('acs5', 2018, geo, variables)

            for variable in variables:
                if variable in value_dict.keys():
                    entry = value_dict[variable]
                    entry.append(census_data[variable][0])
                    value_dict[variable] = entry
                else:
                    value_dict[variable] = [census_data[variable][0]]

    for var in value_dict.keys():
        state_covid_data[var] = value_dict[var]

    if rename_map != {}:
        state_covid_data.rename(columns=rename_map, inplace=True)

    if save:
        state_covid_data.to_csv(output_data_path + f'{state}.csv')

    return state_covid_data


def main():
    args = arg_parser.parse_args()

    if args.interactive:
        logger.info('Starting CoronaFramer in interactive mode')
        state = input('Please enter the state you are interested in: ')
        logger.info(f'Attempting to build frame for {state}')

        build_frame_for_state(state, interest_variables, rename_map=variable_name_map)

        run_again = input('Finished output! Would you like to run the program again? (Y/N) ').lower() == 'y'

        if run_again:
            main()
        else:
            print('Exiting...')
    else:
        logger.info('Starting CoronaFramer in CLI mode')


if __name__ == '__main__':
    main()
