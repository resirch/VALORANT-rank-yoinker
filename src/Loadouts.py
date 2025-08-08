import time
import requests
from colr import color
from src.constants import sockets, hide_names
import json


class Loadouts:
    def __init__(self, Requests, log, colors, Server, current_map):

        self.Requests = Requests
        self.log = log
        self.colors = colors
        self.Server = Server
        self.current_map = current_map

    def get_match_loadouts(self, match_id, players, weaponChoose, valoApiSkins, names, state="game"):
        playersBackup = players
        weaponLists = {}
        valApiWeapons = requests.get("https://valorant-api.com/v1/weapons").json()
        if state == "game":
            team_id = "Blue"
            PlayerInventorys = self.Requests.fetch("glz", f"/core-game/v1/matches/{match_id}/loadouts", "get")
        elif state == "pregame":
            pregame_stats = players
            players = players["AllyTeam"]["Players"]
            team_id = pregame_stats['Teams'][0]['TeamID']
            PlayerInventorys = self.Requests.fetch("glz", f"/pregame/v1/matches/{match_id}/loadouts", "get")
        for player in range(len(players)):
            if team_id == "Red":
                invindex = player + len(players) - len(PlayerInventorys["Loadouts"])
            else:
                invindex = player
            
            # Add safety check to ensure invindex is valid
            if invindex >= len(PlayerInventorys["Loadouts"]) or invindex < 0:
                continue
                
            inv = PlayerInventorys["Loadouts"][invindex]
            if state == "game":
                inv = inv["Loadout"]
            for weapon in valApiWeapons["data"]:
                if weapon["displayName"].lower() == weaponChoose.lower():
                    skin_id = \
                        inv["Items"][weapon["uuid"].lower()]["Sockets"]["bcef87d6-209b-46c6-8b19-fbe40bd95abc"]["Item"][
                            "ID"]
                    for skin in valoApiSkins.json()["data"]:
                        if skin_id.lower() == skin["uuid"].lower():
                            rgb_color = self.colors.get_rgb_color_from_skin(skin["uuid"].lower(), valoApiSkins)
                            # Remove trailing weapon name from skin display (e.g., "Kuronami Vandal" -> "Kuronami")
                            display_name = skin.get("displayName", "")
                            for weapon_obj in valApiWeapons["data"]:
                                weapon_name = weapon_obj.get("displayName", "")
                                if weapon_name and display_name.lower().endswith(" " + weapon_name.lower()):
                                    display_name = display_name[: -len(weapon_name)].rstrip()
                                    break
                            # Shorten to first word, keeping a numeric token (e.g., 2.0) if present anywhere
                            tokens = display_name.split()
                            if tokens:
                                first_word = tokens[0]
                                numeric_tokens = [t for t in tokens if any(ch.isdigit() for ch in t)]
                                if numeric_tokens:
                                    short_name = f"{first_word} {numeric_tokens[-1]}"
                                else:
                                    short_name = first_word
                            else:
                                short_name = display_name
                            weaponLists.update({players[player]["Subject"]: color(short_name, fore=rgb_color)})
                            # else:
                            #     weaponLists.update({player["Subject"]: color(skin["Name"], fore=rgb_color)})
        final_json = self.convertLoadoutToJsonArray(PlayerInventorys, playersBackup, state, names)
        # self.log(f"json for website: {final_json}")
        self.Server.send_payload("matchLoadout",final_json)
        return [weaponLists,final_json]

    #this will convert valorant loadouts to json with player names
    def convertLoadoutToJsonArray(self, PlayerInventorys, players, state, names):
        #get agent dict from main in future
        # names = self.namesClass.get_names_from_puuids(players)
        valoApiSprays = requests.get("https://valorant-api.com/v1/sprays")
        valoApiWeapons = requests.get("https://valorant-api.com/v1/weapons")
        valoApiBuddies = requests.get("https://valorant-api.com/v1/buddies")
        valoApiAgents = requests.get("https://valorant-api.com/v1/agents")
        valoApiTitles = requests.get("https://valorant-api.com/v1/playertitles")
        valoApiPlayerCards = requests.get("https://valorant-api.com/v1/playercards")

        final_final_json = {"Players": {},
                            "time": int(time.time()),
                            "map": self.current_map}

        final_json = final_final_json["Players"]
        if state == "game":
            PlayerInventorys = PlayerInventorys["Loadouts"]
            for i in range(len(PlayerInventorys)):
                PlayerInventory = PlayerInventorys[i]["Loadout"]
                # Add safety check to ensure players[i] exists
                if i < len(players):
                    final_json.update(
                        {
                            players[i]["Subject"]: {}
                        }
                    )
                else:
                    # Skip this iteration if players[i] doesn't exist
                    continue

                # Only process if players[i] exists
                if i < len(players):
                    #creates name field
                    if hide_names:
                        for agent in valoApiAgents.json()["data"]:
                            if agent["uuid"] == players[i]["CharacterID"]:
                                final_json[players[i]["Subject"]].update({"Name": agent["displayName"]})
                    else:
                        final_json[players[i]["Subject"]].update({"Name": names[players[i]["Subject"]]})

                    #creates team field
                    final_json[players[i]["Subject"]].update({"Team": players[i]["TeamID"]})

                    #create spray field
                    final_json[players[i]["Subject"]].update({"Sprays": {}})
                    #append sprays to field

                    final_json[players[i]["Subject"]].update({"Level": players[i]["PlayerIdentity"]["AccountLevel"]})

                    for title in valoApiTitles.json()["data"]:
                        if title["uuid"] == players[i]["PlayerIdentity"]["PlayerTitleID"]:
                            final_json[players[i]["Subject"]].update({"Title": title["titleText"]})


                    for PCard in valoApiPlayerCards.json()["data"]:
                        if PCard["uuid"] == players[i]["PlayerIdentity"]["PlayerCardID"]:
                            final_json[players[i]["Subject"]].update({"PlayerCard": PCard["largeArt"]})

                    for agent in valoApiAgents.json()["data"]:
                        if agent["uuid"] == players[i]["CharacterID"]:
                            final_json[players[i]["Subject"]].update({"AgentArtworkName": agent["displayName"] + "Artwork"})
                            final_json[players[i]["Subject"]].update({"Agent": agent["displayIcon"]})

                    spray_selections = [
                        s for s in PlayerInventory.get("Expressions", {}).get("AESSelections", [])
                        if s.get("TypeID") == "d5f120f8-ff8c-4aac-92ea-f2b5acbe9475"
                    ]
                    for j, spray in enumerate(spray_selections):
                        final_json[players[i]["Subject"]]["Sprays"].update({j: {}})
                        for sprayValApi in valoApiSprays.json()["data"]:
                            if spray["AssetID"].lower() == sprayValApi["uuid"].lower():
                                final_json[players[i]["Subject"]]["Sprays"][j].update({
                                    "displayName": sprayValApi["displayName"],
                                    "displayIcon": sprayValApi["displayIcon"],
                                    "fullTransparentIcon": sprayValApi["fullTransparentIcon"]
                                })

                    #create weapons field
                    final_json[players[i]["Subject"]].update({"Weapons": {}})

                    for skin in PlayerInventory["Items"]:

                        #create skin field
                        final_json[players[i]["Subject"]]["Weapons"].update({skin: {}})

                        for socket in PlayerInventory["Items"][skin]["Sockets"]:
                            #predefined sockets
                            for var_socket in sockets:
                                if socket == sockets[var_socket]:
                                    final_json[players[i]["Subject"]]["Weapons"][skin].update(
                                        {
                                            var_socket: PlayerInventory["Items"][skin]["Sockets"][socket]["Item"]["ID"]
                                        }
                                    )

                        #create buddy field
                        # self.log("predefined sockets")
                        # final_json[players[i]["Subject"]]["Weapons"].update({skin: {}})

                        #buddies
                        for socket in PlayerInventory["Items"][skin]["Sockets"]:
                            if sockets["skin_buddy"] == socket:
                                for buddy in valoApiBuddies.json()["data"]:
                                    if buddy["uuid"] == PlayerInventory["Items"][skin]["Sockets"][socket]["Item"]["ID"]:
                                        final_json[players[i]["Subject"]]["Weapons"][skin].update(
                                            {
                                                "buddy_displayIcon": buddy["displayIcon"]
                                            }
                                        )

                        #append names to field
                        for weapon in valoApiWeapons.json()["data"]:
                            if skin == weapon["uuid"]:
                                final_json[players[i]["Subject"]]["Weapons"][skin].update(
                                    {
                                        "weapon": weapon["displayName"]
                                    }
                                )
                                for skinValApi in weapon["skins"]:
                                    if skinValApi["uuid"] == PlayerInventory["Items"][skin]["Sockets"][sockets["skin"]]["Item"]["ID"]:
                                        # Remove trailing weapon name from skin display (e.g., "Kuronami Vandal" -> "Kuronami")
                                        skin_name = skinValApi["displayName"]
                                        weapon_name = weapon["displayName"]
                                        if skin_name.lower().endswith(" " + weapon_name.lower()):
                                            skin_name = skin_name[: -len(weapon_name)].rstrip()
                                        # Shorten to first word + numeric token if present anywhere
                                        tokens = skin_name.split()
                                        if tokens:
                                            first_word = tokens[0]
                                            numeric_tokens = [t for t in tokens if any(ch.isdigit() for ch in t)]
                                            if numeric_tokens:
                                                skin_name_short = f"{first_word} {numeric_tokens[-1]}"
                                            else:
                                                skin_name_short = first_word
                                        else:
                                            skin_name_short = skin_name
                                        final_json[players[i]["Subject"]]["Weapons"][skin].update(
                                            {
                                                "skinDisplayName": skin_name_short
                                            }
                                        )
                                        for chroma in skinValApi["chromas"]:
                                            if chroma["uuid"] == PlayerInventory["Items"][skin]["Sockets"][sockets["skin_chroma"]]["Item"]["ID"]:
                                                if chroma["displayIcon"] != None:
                                                    final_json[players[i]["Subject"]]["Weapons"][skin].update(
                                                        {
                                                            "skinDisplayIcon": chroma["displayIcon"]
                                                        }
                                                    )
                                                elif chroma["fullRender"] != None:
                                                    final_json[players[i]["Subject"]]["Weapons"][skin].update(
                                                        {
                                                            "skinDisplayIcon": chroma["fullRender"]
                                                        }
                                                    )
                                                elif skinValApi["displayIcon"] != None:
                                                    final_json[players[i]["Subject"]]["Weapons"][skin].update(
                                                        {
                                                            "skinDisplayIcon": skinValApi["displayIcon"]
                                                        }
                                                    )
                                                else:
                                                    final_json[players[i]["Subject"]]["Weapons"][skin].update(
                                                        {
                                                            "skinDisplayIcon": skinValApi["levels"][0]["displayIcon"]
                                                        }
                                                    )
                                        if skinValApi["displayName"].startswith("Standard") or skinValApi["displayName"].startswith("Melee"):
                                            final_json[players[i]["Subject"]]["Weapons"][skin]["skinDisplayIcon"] = weapon["displayIcon"]

        return final_final_json
