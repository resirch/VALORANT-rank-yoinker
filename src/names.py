import json
import requests
import os
from src.constants import hide_names  # import the global flag


class Names:

    def __init__(self, Requests, log):
        self.Requests = Requests
        self.log = log

    def mask_name(self, name):
        # Returns a placeholder if names are to be hidden.
        return "Player"

    def get_stats_data(self):
        try:
            with open(os.path.join(os.getenv('APPDATA'), "vry/stats.json"), "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def check_and_update_name(self, puuid, current_name, force_show=False):
        # If force_show is True, ignore any stored value and update with current full name.
        if force_show:
            return current_name

        # Load stats data to get previous names
        stats_data = self.get_stats_data()
        
        # If we've seen this player before, compare names.
        if puuid in stats_data and len(stats_data[puuid]) > 0:
            # Get the most recent entry for this player
            latest_entry = stats_data[puuid][-1]
            old_name = latest_entry.get("name", "")
            
            if "(now " in old_name:
                old_name = old_name.split(" (now ")[0]
            
            if old_name != current_name and old_name != "":
                return f"{old_name} (now {current_name})"
            else:
                return current_name
        else:
            return current_name

    def get_name_from_puuid(self, puuid, force_show=False):
        response = requests.put(
            self.Requests.pd_url + "/name-service/v2/players",
            headers=self.Requests.get_headers(),
            json=[puuid],
            verify=False
        )
        full_name = response.json()[0]["GameName"] + "#" + response.json()[0]["TagLine"]
        return self.check_and_update_name(puuid, full_name, force_show=force_show)

    def get_multiple_names_from_puuid(self, puuids, force_show=False):
        response = requests.put(
            self.Requests.pd_url + "/name-service/v2/players",
            headers=self.Requests.get_headers(),
            json=puuids,
            verify=False
        )
        if 'errorCode' in response.json():
            self.log(f'{response.json()["errorCode"]}, new token retrieved')
            response = requests.put(
                self.Requests.pd_url + "/name-service/v2/players",
                headers=self.Requests.get_headers(refresh=True),
                json=puuids,
                verify=False
            )

        name_dict = {}
        for player in response.json():
            puuid = player["Subject"]
            full_name = f"{player['GameName']}#{player['TagLine']}"
            name_dict[puuid] = self.check_and_update_name(puuid, full_name, force_show=force_show)
        return name_dict

    def get_names_from_puuids(self, players, force_show=False):
        players_puuid = [player["Subject"] for player in players]
        return self.get_multiple_names_from_puuid(players_puuid, force_show=force_show)

    def get_players_puuid(self, Players):
        return [player["Subject"] for player in Players]
