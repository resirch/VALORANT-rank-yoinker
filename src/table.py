from typing import Literal, get_args

# from prettytable import PrettyTable
from rich.table import Table as RichTable
from rich.console import Console as RichConsole
from rich.table import Table as RichInnerTable

# define constants for all column headers
# avoids "magic strings"
HEADER_PARTY = "Party"
HEADER_AGENT = "Agent"
HEADER_NAME = "Name"
HEADER_SKIN = "Skin"
HEADER_RANK = "Rank"
HEADER_RR = "RR"
HEADER_PEAK_RANK = "Peak Rank"
HEADER_PREVIOUS_RANK = "Previous Act Rank"
HEADER_PREVIOUS_RANK_SHORT = "Last Act"
HEADER_LEADERBOARD_POS = "Pos."
HEADER_HS_PERCENT = "HS"
HEADER_WINRATE = "WR"
HEADER_KD_RATIO = "KD"
HEADER_LEVEL = "Level"
HEADER_EARNED_RR = "ΔRR"


TABLE_COLUMN_NAMES = Literal[
    HEADER_PARTY,
    HEADER_AGENT,
    HEADER_NAME,
    HEADER_SKIN,
    HEADER_RANK,
    HEADER_RR,
    HEADER_PEAK_RANK,
    HEADER_PREVIOUS_RANK,
    HEADER_LEADERBOARD_POS,
    HEADER_HS_PERCENT,
    HEADER_WINRATE,
    HEADER_KD_RATIO,
    HEADER_LEVEL,
    HEADER_EARNED_RR,
]


class Table:
    def __init__(self, config, log):
        self.log = log
        self.config = config
        self.rich_table = RichTable()
        self.col_flags = [
            bool(config.get_feature_flag("party_finder")),  # Party
            True,  # Agent
            True,  # Name
            bool(config.table.get("skin", True)),  # Skin
            True,  # Rank
            bool(config.table.get("rr", True)),  # RR
            bool(config.table.get("peakrank", True)),  # Peak Rank
            bool(config.table.get("previousrank", False)),  # Previous Rank
            bool(config.table.get("leaderboard", True)),  # Leaderboard Position
            bool(config.table.get("headshot_percent", True)),  # hs
            bool(config.table.get("winrate", True)),  # wr
            bool(config.table.get("kd", True)),  # KD
            False,  # Level (temporarily hidden)
            bool(config.table.get("earned_rr", True)),  # Earned RR
        ]
        self.runtime_col_flags = self.col_flags[:]  # making a copy
        
        candidates = list(get_args(TABLE_COLUMN_NAMES))

        # Set column names based on config
        if self.config.get_feature_flag("short_ranks"):
            self.field_names_candidates = [
                HEADER_PREVIOUS_RANK_SHORT if name == HEADER_PREVIOUS_RANK else name
                for name in candidates
            ]
        else:
            self.field_names_candidates = candidates

        if HEADER_SKIN in self.field_names_candidates:
            skin_index = self.field_names_candidates.index(HEADER_SKIN)
            self.field_names_candidates[skin_index] = self.config.weapon.capitalize()
            
        self.field_names = [
            c for c, i in zip(self.field_names_candidates, self.col_flags) if i
        ]
        self.console = RichConsole(color_system="truecolor", width=300)

        # only to get init value not used
        self.overall_col_flags = [
            f1 & f2 for f1, f2 in zip(self.col_flags, self.runtime_col_flags)
        ]
        self.fields_to_display = [
            c
            for c, flag in zip(self.field_names_candidates, self.overall_col_flags)
            if flag
        ]

        # for field in fields_to_display:
        #     self.rich_table.add_column(field, justify="center")
        # self.set_collumns()
        self.rows = []

    def set_title(self, title):
        self.rich_table.title = self.ansi_to_console(title)

    def set_caption(self, caption):
        self.rich_table.caption = self.ansi_to_console(caption)

    def set_default_field_names(self):
        self.rich_table.field_names = self.field_names[:]

    def set_field_names(self, field_names):
        self.rich_table.field_names = field_names

    def make_split_cell(self, left_text: str, right_text: str):
        grid = RichInnerTable.grid(expand=True)
        # Left column
        grid.add_column(justify="left")
        # Spacer column: fixed width to guarantee at least two spaces
        grid.add_column(justify="left", no_wrap=True, width=2)
        # Right column
        grid.add_column(justify="right")
        grid.add_row(
            self.ansi_to_console(left_text),
            "  ",
            self.ansi_to_console(right_text),
        )
        return grid

    def make_center_cell(self, text: str):
        grid = RichInnerTable.grid(expand=True)
        grid.add_column(justify="center")
        grid.add_row(self.ansi_to_console(text))
        return grid

    def add_row_table(self, args: list):
        # Store field/value pairs; convert to a list so we can safely inspect multiple times
        self.rows.append(list(zip(self.field_names_candidates, args)))

    def add_empty_row(self):
        self.rows.append(
            list(zip(self.field_names_candidates, [""] * len(self.field_names_candidates)))
        )

    def apply_rows(self):
        for row in self.rows:
            processed_row = []
            for col_name, value in row:
                if col_name in self.fields_to_display:
                    # Convert basic types to strings
                    if isinstance(value, (int, float, bool)) or value is None:
                        processed_row.append(self.ansi_to_console(str(value)))
                    elif isinstance(value, str):
                        processed_row.append(self.ansi_to_console(value))
                    else:
                        # Assume value is a Rich renderable (e.g., grid)
                        processed_row.append(value)
            self.rich_table.add_row(*processed_row)

    def reset_runtime_col_flags(self):
        self.runtime_col_flags = self.col_flags[:]

    def set_runtime_col_flag(self, field_name: str, flag: bool):
        try:
            index = self.field_names_candidates.index(field_name)
            self.runtime_col_flags[index] = flag
        except ValueError:
            self.log(f"Warning: Attempted to set a flag for a non-existent column: {field_name}")


    def display(self):
        self.log("rows: " + str(self.rows))
        self.set_columns()
        self.apply_rows()

        self.console.print(self.rich_table)

    def clear(self):
        self.rich_table = RichTable()
        self.rows = []
        self.rich_table.title_style = "bold"
        self.rich_table.caption_style = "italic rgb(50,505,50)"
        self.rich_table.caption_justify = "left"

        pass

    def ansi_to_console(self, line):
        if not isinstance(line, str):
            return line
        if "\x1b[38;2;" not in line:
            return line
        string_to_return = ""
        strings = line.split("\x1b[38;2;")
        del strings[0]
        for string in strings:
            splits = string.split("m", 1)
            rgb = [int(i) for i in splits[0].split(";")]
            original_strings = splits[1].split("\x1b[0m")
            string_to_return += (
                f"[rgb({rgb[0]},{rgb[1]},{rgb[2]})]{'[/]'.join(original_strings)}"
            )
        return string_to_return

    def set_columns(self):
        self.overall_col_flags = [
            f1 & f2 for f1, f2 in zip(self.col_flags, self.runtime_col_flags)
        ]
        self.fields_to_display = [
            c
            for c, flag in zip(self.field_names_candidates, self.overall_col_flags)
            if flag
        ]

        # Dynamically include the Party column only if any row has a party icon/value
        if "Party" in self.fields_to_display:
            has_party = any(
                any(col_name == "Party" and str(value).strip() != "" for col_name, value in row)
                for row in self.rows
            )
            if not has_party:
                self.fields_to_display = [f for f in self.fields_to_display if f != "Party"]

        skin_column_name = self.config.weapon.capitalize()

        # Columns that should never be truncated
        static_overflow_fold_columns = {
            HEADER_HS_PERCENT,
            HEADER_KD_RATIO,
            HEADER_LEVEL,
            HEADER_LEADERBOARD_POS,
        }

        # Conditional columns
        conditional_columns = {
            HEADER_NAME: "truncate_names",
            skin_column_name: "truncate_skins",
        }

        for field in self.fields_to_display:
            # Base properties for all columns
            kwargs = {"justify": "center"}
            apply_fold = False

            # Special handling for specific columns
            if field in ("Rank", "Peak Rank"):
                # Center the column (header centered), prevent wrapping
                kwargs["no_wrap"] = True
            elif field == "RR":
                kwargs["justify"] = "right"
            elif field == "Name":
                # Keep on one line and ellipsize when too long; center, with a sane max width
                kwargs.update({"no_wrap": True, "overflow": "ellipsis", "max_width": 14})
            elif field == "Skin":
                # Keep skin on one line and ellipsize with a capped width
                kwargs.update({"no_wrap": True, "overflow": "ellipsis", "max_width": 18})
            elif field == "Party":
                # Show party column with no header text
                self.rich_table.add_column("", justify="center", no_wrap=True)
                continue

            # Check if the column should always fold (not truncated)
            if field in static_overflow_fold_columns:
                apply_fold = True
            # Check flags
            elif field in conditional_columns:
                flag_name = conditional_columns[field]
                if not self.config.get_feature_flag(flag_name):
                    apply_fold = True

            # Apply
            if apply_fold:
                kwargs["overflow"] = "fold"

            # Columns without rules use base args
            self.rich_table.add_column(field, **kwargs)
