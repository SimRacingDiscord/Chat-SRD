import datetime
from iracingdataapi.client import irDataClient
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

load_dotenv()


def ms_to_laptime(ms):
    total_secs = ms / 10000
    minutes = int(total_secs // 60)
    seconds = int(total_secs % 60)
    remaining_ms = int(ms % 1000)
    return f"{minutes}:{seconds:02d}.{remaining_ms:03d}"


class IR_Handler:
    def __init__(self):
        username = os.getenv("IR_USER")
        password = os.getenv("IR_PASSWORD")
        self.api = irDataClient(username=username, password=password)

    def convtime(self):
        return datetime.timedelta(milliseconds=self).total_seconds()

    def lookup_driver(self, display_name):
        drivers = self.api.lookup_drivers(display_name)
        if drivers:  # check if list is not empty
            return drivers[0]["cust_id"]

    def get_recentincidents(self, *display_names):
        incidents = []
        names = []
        for name in display_names:
            names.append(name)
            driver_id = self.lookup_driver(name)  # Corrected here
            recentraces = self.api.stats_member_recent_races(driver_id)
            driver_incidents = sum(race["incidents"] for race in recentraces["races"])
            incidents.append(driver_incidents)
        return dict(zip(names, incidents))

    def get_member_bests(self, display_name):
        driver_id = self.lookup_driver(display_name)
        return self.api.stats_member_bests(driver_id)
    
    def get_member_stats(self, display_name):
        driver_id = self.lookup_driver(display_name)
        return self.api.stats_member_career(driver_id)

    def get_member_irating_chart(self, *display_names):
        chart_data = []
        for name in display_names:
            driver_id = self.lookup_driver(name)
            data = self.api.member_chart_data(driver_id)
            chart_data.append(data)
        return dict(zip(display_names, chart_data))

    def get_member_last_race(self, display_name):
        driver_id = self.lookup_driver(display_name)
        return self.api.stats_member_recent_races(driver_id)["races"][0]

    def get_result_lap_data(self, display_name, subsession_id):
        cust_id = self.lookup_driver(display_name)
        race_results = self.api.result_lap_data(
            cust_id=cust_id, subsession_id=subsession_id
        )
        lap_times = []
        for lap in race_results:
            lap_times.append(lap["lap_time"])
        return lap_times

    def get_subsession(self, subsession_id):
        return self.api.result(subsession_id)

    def get_result(self, subsession_id):
        return self.api.result(subsession_id)

    def get_carmodel(self, car_id):
        cars_list = self.api.get_cars()
        car_id_tomatch = car_id
        matching_cars = []
        for car in cars_list:
            if car["car_id"] == car_id_tomatch:
                matching_cars.append(car["car_name"])
        return (matching_cars)[0]
    
    def get_current_year_season(self):
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        if month < 4:
            quarter = 1
        elif month < 7:
            quarter = 2
        elif month < 10:
            quarter = 3
        else:
            quarter = 4
        return year, quarter

    def get_eventlist(self, season_year, season_quarter):
        if season_year is None or season_quarter is None:
            season_year, season_quarter = self.get_current_year_season()
        return self.api.season_list(season_year, season_quarter)

    def get_laptimes(self, display_name, subsession_id=None):
        cust_id = self.lookup_driver(display_name)
        if subsession_id is not None:
            subsession_id = int(subsession_id)
        else:
            subsession_id = self.api.stats_member_recent_races(cust_id)["races"][0][
                "subsession_id"
            ]

        try:
            lap_data = self.api.result_lap_data(
                cust_id=cust_id, subsession_id=subsession_id
            )
        except RuntimeError as e:
            print(e.args[1].text)  # Prints the error message from the API
            raise e

        lap_times = [lap["lap_time"] for lap in lap_data]
        lap_times = [lap for lap in lap_times if lap != -1][1:]  # exclude the first lap
        lap_numbers = list(range(1, len(lap_times) + 1))
        return dict(zip(lap_numbers, lap_times))

    def get_race_position_data(self, subsession_id):
        data = self.api.result_lap_chart_data(subsession_id=subsession_id)
        return data

    def get_stats_member_recent_races(self, cust_id):
        cust_id = self.lookup_driver(cust_id)
        recent_races = self.api.stats_member_recent_races(cust_id)['races']
        return recent_races