import json
import os
import re
import time
import requests


# ============================================================
#                    CONFIGURATION
# ============================================================

API_URL = "https://sim-data.athex-black-hat.workers.dev/"


# ============================================================
#                       COLORS
# ============================================================

class Color:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


# ============================================================
#                    TERMINAL UI
# ============================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def line(char="─", length=68):
    print(Color.CYAN + char * length + Color.RESET)


def pause():
    input(
        "\n"
        + Color.DIM
        + "Press ENTER to continue..."
        + Color.RESET
    )


def loading(text="Processing"):
    print(
        Color.YELLOW
        + f"\n[•] {text}"
        + Color.RESET,
        end=""
    )

    for _ in range(3):
        time.sleep(0.25)
        print(".", end="", flush=True)

    print()


def success(text):
    print(
        Color.GREEN
        + f"\n[✓] {text}"
        + Color.RESET
    )


def error(text):
    print(
        Color.RED
        + f"\n[!] {text}"
        + Color.RESET
    )


def info(text):
    print(
        Color.CYAN
        + f"[i] {text}"
        + Color.RESET
    )


# ============================================================
#                         BANNER
# ============================================================

def banner():
    print(
        Color.CYAN
        + r"""
    ██████╗ ██████╗ ██╗███╗   ██╗ ██████╗███████╗
    ██╔══██╗██╔══██╗██║████╗  ██║██╔════╝██╔════╝
    ██████╔╝██████╔╝██║██╔██╗ ██║██║     █████╗
    ██╔═══╝ ██╔══██╗██║██║╚██╗██║██║     ██╔══╝
    ██║     ██║  ██║██║██║ ╚████║╚██████╗███████╗
    ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
    """
        + Color.RESET
    )

    print(
        Color.BOLD
        + Color.WHITE
        + "                 PRINCE CODER"
        + Color.RESET
    )

    print(
        Color.DIM
        + "                 API  •  JSON  •  CLI"
        + Color.RESET
    )

    print()


# ============================================================
#                    PHONE FUNCTIONS
# ============================================================

def normalize_phone(number):
    number = re.sub(
        r"[\s\-+]",
        "",
        number.strip()
    )

    if number.startswith("92"):
        number = "0" + number[2:]

    return number


def validate_phone(number):
    number = normalize_phone(number)

    return bool(
        re.fullmatch(
            r"03\d{9}",
            number
        )
    )


# ============================================================
#                     CNIC FUNCTIONS
# ============================================================

def normalize_cnic(cnic):
    cnic = re.sub(
        r"[-\s]",
        "",
        cnic.strip()
    )

    if re.fullmatch(r"\d{13}", cnic):
        cnic = (
            cnic[:5]
            + "-"
            + cnic[5:12]
            + "-"
            + cnic[12]
        )

    return cnic


def validate_cnic(cnic):
    clean_cnic = re.sub(
        r"[-\s]",
        "",
        cnic.strip()
    )

    return bool(
        re.fullmatch(
            r"\d{13}",
            clean_cnic
        )
    )


# ============================================================
#                  JSON DISPLAY FUNCTIONS
# ============================================================

def format_key(key):
    key = str(key)
    key = key.replace("_", " ")
    key = key.replace("-", " ")

    return key.title()


def display_json(data, indent=0):
    spacing = " " * indent

    if isinstance(data, dict):

        for key, value in data.items():

            if isinstance(value, (dict, list)):

                print(
                    Color.CYAN
                    + spacing
                    + format_key(key)
                    + ":"
                    + Color.RESET
                )

                display_json(
                    value,
                    indent + 4
                )

            else:

                print(
                    spacing
                    + Color.WHITE
                    + f"{format_key(key):20}"
                    + Color.RESET
                    + ": "
                    + Color.GREEN
                    + str(value)
                    + Color.RESET
                )

    elif isinstance(data, list):

        for item in data:

            if isinstance(
                item,
                (dict, list)
            ):

                display_json(
                    item,
                    indent
                )

            else:

                print(
                    spacing
                    + Color.GREEN
                    + "• "
                    + str(item)
                    + Color.RESET
                )


# ============================================================
#              FIND SELECTED PHONE RECORD
# ============================================================

def find_phone_record(data, number):

    phone_keys = {
        "phone",
        "phone_number",
        "number",
        "mobile",
        "mobile_number",
        "msisdn"
    }

    if isinstance(data, dict):

        for key, value in data.items():

            if (
                str(key).lower()
                in phone_keys
            ):

                if normalize_phone(
                    str(value)
                ) == number:

                    return data

            result = find_phone_record(
                value,
                number
            )

            if result:
                return result

    elif isinstance(data, list):

        for item in data:

            result = find_phone_record(
                item,
                number
            )

            if result:
                return result

    return None


# ============================================================
#                  GET FIELD FROM RECORD
# ============================================================

def get_field(record, possible_keys):

    if not isinstance(record, dict):
        return None

    for key in possible_keys:

        for actual_key, value in record.items():

            if (
                str(actual_key).lower()
                == key.lower()
            ):

                return value

    return None


# ============================================================
#                EXTRACT LINKED NUMBERS
# ============================================================

def extract_linked_numbers(data):

    phone_keys = {
        "phone",
        "phone_number",
        "number",
        "mobile",
        "mobile_number",
        "msisdn"
    }

    location_keys = {
        "location",
        "city",
        "area",
        "address"
    }

    name_keys = {
        "name",
        "full_name",
        "username",
        "customer_name",
        "owner_name"
    }

    sim_keys = {
        "sim",
        "sim_name",
        "network",
        "operator",
        "company",
        "carrier",
        "sim_network"
    }

    cnic_keys = {
        "cnic",
        "nic",
        "national_id",
        "id_number"
    }

    results = []

    def scan(obj):

        if isinstance(obj, dict):

            phone = None
            location = None
            name = None
            sim = None
            cnic = None

            # ----------------------------------------
            # PHONE
            # ----------------------------------------

            for key, value in obj.items():

                if (
                    str(key).lower()
                    in phone_keys
                ):

                    possible_phone = normalize_phone(
                        str(value)
                    )

                    if validate_phone(
                        possible_phone
                    ):

                        phone = possible_phone
                        break

            # ----------------------------------------
            # LOCATION
            # ----------------------------------------

            for key, value in obj.items():

                if (
                    str(key).lower()
                    in location_keys
                ):

                    location = str(value)
                    break

            # ----------------------------------------
            # NAME
            # ----------------------------------------

            for key, value in obj.items():

                if (
                    str(key).lower()
                    in name_keys
                ):

                    name = str(value)
                    break

            # ----------------------------------------
            # SIM / NETWORK
            # ----------------------------------------

            for key, value in obj.items():

                if (
                    str(key).lower()
                    in sim_keys
                ):

                    sim = str(value)
                    break

            # ----------------------------------------
            # CNIC
            # ----------------------------------------

            for key, value in obj.items():

                if (
                    str(key).lower()
                    in cnic_keys
                ):

                    cnic = str(value)
                    break

            # ----------------------------------------
            # SAVE RESULT
            # ----------------------------------------

            if phone:

                exists = False

                for item in results:

                    if item["number"] == phone:
                        exists = True
                        break

                if not exists:

                    results.append({
                        "number": phone,
                        "name": name,
                        "cnic": cnic,
                        "sim": sim,
                        "location": location
                    })

            # ----------------------------------------
            # RECURSIVE SEARCH
            # ----------------------------------------

            for value in obj.values():
                scan(value)

        elif isinstance(obj, list):

            for item in obj:
                scan(item)

    scan(data)

    return results


# ============================================================
#                  PHONE INFORMATION
# ============================================================

def phone_information():

    clear_screen()
    banner()

    print(
        Color.BOLD
        + Color.WHITE
        + "PHONE INFORMATION"
        + Color.RESET
    )

    line()

    number = input(
        Color.YELLOW
        + "\nEnter phone number: "
        + Color.RESET
    )

    number = normalize_phone(number)

    if not validate_phone(number):

        error(
            "Invalid phone number. Example: 03001234567"
        )

        pause()
        return

    loading("Querying API")

    try:

        response = requests.get(
            API_URL,
            params={
                "search": number
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as exception:

        error(
            f"API request failed: {exception}"
        )

        pause()
        return

    except ValueError:

        error(
            "API returned invalid JSON."
        )

        pause()
        return

    record = find_phone_record(
        data,
        number
    )

    if not record:

        error(
            "No matching record found."
        )

        pause()
        return

    # ========================================================
    #                    RESULT CARD
    # ========================================================

    print()

    print(
        Color.MAGENTA
        + "╔══════════════════════════════════════════════════════════╗"
        + Color.RESET
    )

    print(
        Color.MAGENTA
        + "║"
        + Color.WHITE
        + "                  PHONE PROFILE                         "
        + Color.MAGENTA
        + "║"
        + Color.RESET
    )

    print(
        Color.MAGENTA
        + "╠══════════════════════════════════════════════════════════╣"
        + Color.RESET
    )

    phone = get_field(
        record,
        [
            "phone",
            "phone_number",
            "number",
            "mobile",
            "mobile_number",
            "msisdn"
        ]
    )

    name = get_field(
        record,
        [
            "name",
            "full_name",
            "username",
            "customer_name",
            "owner_name"
        ]
    )

    cnic = get_field(
        record,
        [
            "cnic",
            "nic",
            "national_id",
            "id_number"
        ]
    )

    sim = get_field(
        record,
        [
            "sim",
            "sim_name",
            "network",
            "operator",
            "carrier",
            "company",
            "sim_network"
        ]
    )

    location = get_field(
        record,
        [
            "location",
            "city",
            "area",
            "address"
        ]
    )

    status = get_field(
        record,
        [
            "status"
        ]
    )

    fields = [

        ("PHONE", phone or number),

        ("NAME", name or "Not provided"),

        ("CNIC", cnic or "Not provided"),

        ("SIM / NETWORK", sim or "Not provided"),

        ("LOCATION", location or "Not provided"),

        ("STATUS", status or "Not provided")

    ]

    for key, value in fields:

        print(
            Color.MAGENTA
            + "║ "
            + Color.CYAN
            + f"{key:<17}"
            + Color.WHITE
            + ": "
            + Color.GREEN
            + str(value)
            + Color.RESET
        )

    print(
        Color.MAGENTA
        + "╚══════════════════════════════════════════════════════════╝"
        + Color.RESET
    )

    print()

    info("Additional API fields:")

    display_json(
        record,
        4
    )

    pause()


# ============================================================
#                    CNIC INFORMATION
# ============================================================

def cnic_information():

    clear_screen()
    banner()

    print(
        Color.BOLD
        + Color.WHITE
        + "CNIC INFORMATION"
        + Color.RESET
    )

    line()

    cnic = input(
        Color.YELLOW
        + "\nEnter CNIC: "
        + Color.RESET
    )

    if not validate_cnic(cnic):

        error(
            "Invalid CNIC. Example: 12345-1234567-1"
        )

        pause()
        return

    cnic = normalize_cnic(cnic)

    loading("Searching linked records")

    try:

        response = requests.get(
            API_URL,
            params={
                "search": cnic
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as exception:

        error(
            f"API request failed: {exception}"
        )

        pause()
        return

    except ValueError:

        error(
            "API returned invalid JSON."
        )

        pause()
        return

    results = extract_linked_numbers(data)

    if not results:

        error(
            "No linked numbers found."
        )

        pause()
        return

    # ========================================================
    #                    CNIC HEADER
    # ========================================================

    print()

    print(
        Color.MAGENTA
        + "╔══════════════════════════════════════════════════════════╗"
        + Color.RESET
    )

    print(
        Color.MAGENTA
        + "║"
        + Color.WHITE
        + "                    CNIC PROFILE                        "
        + Color.MAGENTA
        + "║"
        + Color.RESET
    )

    print(
        Color.MAGENTA
        + "╠══════════════════════════════════════════════════════════╣"
        + Color.RESET
    )

    print(
        Color.MAGENTA
        + "║ "
        + Color.CYAN
        + "CNIC"
        + Color.WHITE
        + "              : "
        + Color.GREEN
        + cnic
        + Color.RESET
    )

    print(
        Color.MAGENTA
        + "║ "
        + Color.CYAN
        + "LINKED NUMBERS"
        + Color.WHITE
        + "     : "
        + Color.GREEN
        + str(len(results))
        + Color.RESET
    )

    print(
        Color.MAGENTA
        + "╚══════════════════════════════════════════════════════════╝"
        + Color.RESET
    )

    # ========================================================
    #                    LINKED NUMBERS
    # ========================================================

    print()

    for index, item in enumerate(
        results,
        start=1
    ):

        print(
            Color.CYAN
            + f"┌─── [{index}] "
            + Color.WHITE
            + "NUMBER PROFILE"
            + Color.RESET
        )

        print(
            Color.CYAN
            + "│"
            + Color.RESET
        )

        print(
            Color.CYAN
            + "├── "
            + Color.WHITE
            + "Number"
            + Color.RESET
            + "   : "
            + Color.GREEN
            + str(
                item.get("number")
                or "Not provided"
            )
            + Color.RESET
        )

        print(
            Color.CYAN
            + "├── "
            + Color.WHITE
            + "Name"
            + Color.RESET
            + "     : "
            + Color.GREEN
            + str(
                item.get("name")
                or "Not provided"
            )
            + Color.RESET
        )

        print(
            Color.CYAN
            + "├── "
            + Color.WHITE
            + "CNIC"
            + Color.RESET
            + "      : "
            + Color.GREEN
            + str(
                item.get("cnic")
                or cnic
            )
            + Color.RESET
        )

        print(
            Color.CYAN
            + "├── "
            + Color.WHITE
            + "SIM"
            + Color.RESET
            + "       : "
            + Color.GREEN
            + str(
                item.get("sim")
                or "Not provided"
            )
            + Color.RESET
        )

        print(
            Color.CYAN
            + "├── "
            + Color.WHITE
            + "Location"
            + Color.RESET
            + " : "
            + Color.GREEN
            + str(
                item.get("location")
                or "Not provided"
            )
            + Color.RESET
        )

        print(
            Color.CYAN
            + "└────────────────────────────────────────────────────────"
            + Color.RESET
        )

        print()

    pause()


# ============================================================
#                       MAIN MENU
# ============================================================

def main():

    while True:

        clear_screen()
        banner()

        print(
            Color.WHITE
            + "┌──────────────────────────────────────────────────────────┐"
            + Color.RESET
        )

        print(
            Color.WHITE
            + "│ "
            + Color.CYAN
            + "[1]"
            + Color.WHITE
            + "  Phone Information"
            + Color.RESET
            + "                              │"
        )

        print(
            Color.WHITE
            + "│ "
            + Color.CYAN
            + "[2]"
            + Color.WHITE
            + "  CNIC Information"
            + Color.RESET
            + "                               │"
        )

        print(
            Color.WHITE
            + "│ "
            + Color.RED
            + "[3]"
            + Color.WHITE
            + "  Exit"
            + Color.RESET
            + "                                             │"
        )

        print(
            Color.WHITE
            + "└──────────────────────────────────────────────────────────┘"
            + Color.RESET
        )

        choice = input(
            Color.YELLOW
            + "\nPRINCE CODER > "
            + Color.RESET
        ).strip()

        if choice == "1":

            phone_information()

        elif choice == "2":

            cnic_information()

        elif choice == "3":

            clear_screen()

            print(
                Color.CYAN
                + "\n[✓] PRINCE CODER closed."
                + Color.RESET
            )

            break

        else:

            error(
                "Invalid option."
            )

            time.sleep(1)


# ============================================================
#                         START
# ============================================================

if __name__ == "__main__":
    main() 