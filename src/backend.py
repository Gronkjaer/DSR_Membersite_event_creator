# ------------------------------
# Backend data handling
# ------------------------------
# This module contains all data processing, validation,
# file I/O, encryption, and configuration functions.
# It does not contain any GUI code.
#
# Author: Jonas Groenkjaer Pedersen
# ------------------------------


# ------------------------------
# Packages
# ------------------------------
import ast
import datetime
import json
import os
import pathlib
import pickle
from typing import Callable

from utils import CheckType


# ------------------------------
# Encryption functions
# ------------------------------
def _xor_cipher(text: str, secret: str) -> str:
    """Apply XOR cipher to text using a secret key.

    Parameters
    ----------
    text : str
        The text to encrypt or decrypt.
    secret : str
        The secret key for the XOR cipher.

    Returns
    -------
    str
        The XOR-ciphered result.
    """
    # Validate input types.
    CheckType.is_str(text)
    CheckType.is_str(secret)

    # Apply XOR cipher character by character.
    result = ""
    secret_len = len(secret)
    for i in range(len(text)):
        key_char = secret[i % secret_len]
        xor_val = ord(text[i]) ^ ord(key_char)
        result += chr(xor_val)

    return result


def _to_hex(text: str) -> str:
    """Convert a string to hexadecimal representation.

    Parameters
    ----------
    text : str
        The text to convert.

    Returns
    -------
    str
        Hexadecimal string representation.
    """
    # Validate input type.
    CheckType.is_str(text)

    # Convert each character to two hex digits.
    hex_chars = "0123456789abcdef"
    result = ""
    for c in text:
        val = ord(c)
        result += hex_chars[val >> 4]
        result += hex_chars[val & 15]

    return result


def _from_hex(hex_string: str) -> str:
    """Convert a hexadecimal string back to plain text.

    Parameters
    ----------
    hex_string : str
        The hex string to convert.

    Returns
    -------
    str
        The decoded plain text.
    """
    # Validate input type.
    CheckType.is_str(hex_string)

    # Convert each pair of hex digits back to a character.
    hex_chars = "0123456789abcdef"
    result = ""
    for i in range(0, len(hex_string), 2):
        high = hex_chars.index(hex_string[i])
        low = hex_chars.index(hex_string[i + 1])
        result += chr((high << 4) + low)

    return result


def encrypt_string(text: str, secret: str) -> str:
    """Encrypt a string using XOR cipher and hex encoding.

    Parameters
    ----------
    text : str
        The plaintext to encrypt.
    secret : str
        The secret key.

    Returns
    -------
    str
        The encrypted hex string.
    """
    # Validate input types.
    CheckType.is_str(text)
    CheckType.is_str(secret)

    return _to_hex(_xor_cipher(text, secret))


def decrypt_string(text: str, secret: str) -> str:
    """Decrypt a hex-encoded XOR-ciphered string.

    Parameters
    ----------
    text : str
        The encrypted hex string.
    secret : str
        The secret key.

    Returns
    -------
    str
        The decrypted plaintext.
    """
    # Validate input types.
    CheckType.is_str(text)
    CheckType.is_str(secret)

    return _xor_cipher(_from_hex(text), secret)


def encrypt_dict(data: dict, secret: str | None = None) -> dict:
    """Encrypt all keys and values in a dictionary.

    Parameters
    ----------
    data : dict
        The dictionary to encrypt.
    secret : str | None
        The secret key. If None, uses the user's home
        directory path.

    Returns
    -------
    dict
        Dictionary with encrypted keys and values.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Use home directory as default secret.
    if secret is None:
        secret = str(pathlib.Path.home())

    # Encrypt each key-value pair.
    encrypted = {}
    for k, v in data.items():
        ek = encrypt_string(str(k), secret)
        ev = encrypt_string(str(v), secret)
        encrypted[ek] = ev

    return encrypted


def decrypt_dict(data: dict, secret: str | None = None) -> dict:
    """Decrypt all keys and values in a dictionary.

    Parameters
    ----------
    data : dict
        Dictionary with encrypted keys and values.
    secret : str | None
        The secret key. If None, uses the user's home
        directory path.

    Returns
    -------
    dict
        Dictionary with decrypted keys and values.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Use home directory as default secret.
    if secret is None:
        secret = str(pathlib.Path.home())

    # Decrypt each key-value pair.
    decrypted = {}
    for k, v in data.items():
        dk = decrypt_string(k, secret)
        dv = decrypt_string(v, secret)
        decrypted[dk] = dv

    return decrypted


# ------------------------------
# File I/O functions
# ------------------------------
def get_filepath_of_user_inputs() -> pathlib.Path:
    """Return filepath for stored user inputs.

    Returns
    -------
    pathlib.Path
        Path to the user inputs JSON file.
    """
    filename = "User inputs for Membersite event creator (can safely be deleted).json"
    filepath = pathlib.Path.home() / filename

    return filepath


def get_filepath_of_previous_events() -> pathlib.Path:
    """Return filepath for stored previous events.

    Returns
    -------
    pathlib.Path
        Path to the previous events pickle file.
    """
    filepath = pathlib.Path.home() / "previous_Membersite_events.pkl"

    return filepath


def read_previous_events() -> list[dict[str, str | datetime.datetime]]:
    """Load previously created events from disk.

    Returns
    -------
    list[dict[str, str | datetime.datetime]]
        List of previous event dictionaries, or empty
        list if none exist or reading fails.
    """
    try:
        filepath = get_filepath_of_previous_events()

        # Check if the file exists before reading.
        if filepath.exists():
            with open(filepath, "rb") as file:
                previous_events = pickle.load(file)
        else:
            previous_events = []
    except Exception:
        previous_events = []

    return previous_events


def store_previous_events(
    previous_events: list[dict[str, str | datetime.datetime]],
) -> None:
    """Save the list of previous events to disk.

    Parameters
    ----------
    previous_events : list
        List of event dictionaries to save.
    """
    # Validate input type.
    CheckType.is_list(previous_events)

    # Write the events to a pickle file.
    filepath = get_filepath_of_previous_events()
    with open(filepath, "wb") as file:
        pickle.dump(previous_events, file)

    return None


def save_user_inputs(user_data: dict) -> None:
    """Save user inputs to an encrypted JSON file.

    Parameters
    ----------
    user_data : dict
        The user input data to save.
    """
    # Validate input type.
    CheckType.is_dict(user_data)

    # Encrypt and save to JSON.
    filepath = get_filepath_of_user_inputs()
    encrypted_user_data = encrypt_dict(user_data)
    with open(filepath, "w") as file:
        json.dump(encrypted_user_data, file)

    return None


def load_stored_user_inputs() -> dict | None:
    """Load stored user inputs from the encrypted JSON file.

    Returns
    -------
    dict | None
        Decrypted user inputs, or None if no stored
        inputs exist or reading fails.
    """
    filepath = get_filepath_of_user_inputs()

    # Return None if no stored inputs exist.
    if not filepath.exists():
        return None

    # Load and decrypt the stored inputs.
    try:
        with open(filepath, "r") as file:
            encrypted_user_fields = json.load(file)
        decrypted_fields = decrypt_dict(encrypted_user_fields)
        return decrypted_fields
    except Exception:
        return None


# ------------------------------
# Configuration functions
# ------------------------------
def get_version_info() -> dict[str, str]:
    """Return version information about this application.

    Returns
    -------
    dict[str, str]
        Dictionary with release date, version number,
        and developer name.
    """
    version_info = {
        "Udgivelsestidspunkt": "April 2026",
        "Version": "1.1",
        "Udvikler": "Jonas Grønkjær Pedersen",
    }

    return version_info


def get_default_values_that_may_be_used() -> dict[str, str]:
    """Return default values for optional fields.

    Returns
    -------
    dict[str, str]
        Default values keyed by field name.
    """
    default_values = {
        "Maks antal deltagere": "40",
        "Tidligste tilmelding (antal dage før)": "30",
        "Seneste tilmelding (antal timer før)": "0",
        "Deltagerliste vist indtil (antal dage efter)": "365",
    }

    # Derived defaults (same as existing defaults).
    default_values["Deltagerliste vist fra (antal dage før)"] = default_values["Tidligste tilmelding (antal dage før)"]
    default_values["Seneste afmelding (antal timer før)"] = default_values["Seneste tilmelding (antal timer før)"]

    return default_values


def get_fields() -> dict:
    """Return field definitions for the GUI input form.

    Each field is a list of
    [use_by_default, default_value, hover_text].

    Returns
    -------
    dict
        Field definitions keyed by field name.
    """
    fields = {
        "Email": [
            True,
            "",
            "Email for at logge ind.",
        ],
        "Adgangskode": [
            True,
            "",
            "Adgangskode for at logge ind.",
        ],
        "Navn på gruppe": [
            True,
            "",
            "Gruppe hvor arrangementet skal oprettes.",
        ],
        "Navn på skabelon": [
            True,
            "",
            "Skabelon der anvendes til at oprette arrangementet.",
        ],
        "Første dato": [
            True,
            datetime.datetime.now().date().strftime("%d-%m-%Y"),
            "Første og sidste dato hvor arrangementet skal oprettes (DD-MM-YYYY)."
            + "\nHvis ikke arrangementet er gentagende, så udfyld kun første dato.",
        ],
        "Sidste dato": [
            True,
            "",
            "Første og sidste dato hvor arrangementet skal oprettes (DD-MM-YYYY)."
            + "\nHvis ikke arrangementet er gentagende, så udfyld kun første dato.",
        ],
        "Starttidspunkt": [
            True,
            "11:00",
            "Start- og sluttidspunkt for arrangementet (HH:MM).",
        ],
        "Sluttidspunkt": [
            True,
            "12:00",
            "Start- og sluttidspunkt for arrangementet (HH:MM).",
        ],
        "Titel": [
            True,
            "Tester-begivenhed",
            "Arrangementets titel.",
        ],
        "Sted": [
            True,
            "",
            "VALGFRI: Mødested.",
        ],
        "Maks antal deltagere": [
            True,
            "",
            "Maks antal deltagere.",
        ],
        "Tidligste tilmelding (antal dage før)": [
            True,
            "",
            "Hvornår må man tidligst tilmelde sig (antal dage før starttidspunt)?",
        ],
        "Seneste tilmelding (antal timer før)": [
            True,
            "",
            "Hvornår må man senest tilmelde sig (antal timer før starttidspunt)?",
        ],
        "Seneste afmelding (antal timer før)": [
            True,
            "",
            "Hvornår må man senest afmelde sig (antal timer før starttidspunt)?",
        ],
        "Deltagerliste vist fra (antal dage før)": [
            True,
            "",
            "Hvornår skal deltagerlisten være synlig fra (antal dage før starttidspunt)?",
        ],
        "Deltagerliste vist indtil (antal dage efter)": [
            True,
            "",
            "Hvornår skal deltagerlisten ikke længere kunne ses (antal dage efter sluttidspunkt)?",
        ],
        "Tekst": [
            True,
            "",
            "VALGFRI: Beskrivende tekst.",
        ],
    }

    # Copy explanation for date and time (shared labels in GUI).
    fields["Sidste dato"][2] = fields["Første dato"][2]
    fields["Sluttidspunkt"][2] = fields["Starttidspunkt"][2]

    return fields


def get_radiobutton_options() -> list[str]:
    """Return options for the weekly repetition selector.

    Returns
    -------
    list[str]
        List of repeat options in Danish.
    """
    options = [
        "Ingen gentagelse",
        "Mandag",
        "Tirsdag",
        "Onsdag",
        "Torsdag",
        "Fredag",
        "Lørdag",
        "Søndag",
    ]

    return options


# ------------------------------
# Translation
# ------------------------------
def translate_weekday_from_english_to_danish(weekday: str) -> str:
    """Translate an English weekday name to Danish.

    Parameters
    ----------
    weekday : str
        English weekday name (e.g. "Monday").

    Returns
    -------
    str
        Danish weekday name (e.g. "Mandag").
    """
    # Validate input type.
    CheckType.is_str(weekday)

    # Mapping from English to Danish.
    translate = {
        "Monday": "Mandag",
        "Tuesday": "Tirsdag",
        "Wednesday": "Onsdag",
        "Thursday": "Torsdag",
        "Friday": "Fredag",
        "Saturday": "Lørdag",
        "Sunday": "Søndag",
    }

    weekday_in_danish = translate[weekday]

    return weekday_in_danish


# ------------------------------
# Event helper functions
# ------------------------------
def get_subset_of_event(
    event: dict[str, str | datetime.datetime | None],
) -> dict[str, str | datetime.datetime]:
    """Return a subset of the event for duplicate detection.

    Parameters
    ----------
    event : dict
        Full event dictionary.

    Returns
    -------
    dict[str, str | datetime.datetime]
        Subset with title, group name, start and end
        time.
    """
    # Validate input type and types of required fields.
    CheckType.is_dict(event)
    CheckType.is_str(event["Titel"])
    CheckType.is_str(event["Navn på gruppe"])
    CheckType.is_datetime(event["Start time"])
    CheckType.is_datetime(event["End time"])

    # Build subset dictionary.
    subset_of_event = {
        "Titel": event["Titel"],
        "Navn på gruppe": event["Navn på gruppe"],
        "Start time": event["Start time"],
        "End time": event["End time"],
    }

    return subset_of_event  # type: ignore


def use_default_values_if_not_entered(user_data: dict) -> dict:
    """Fill missing values with defaults where applicable.

    Parameters
    ----------
    user_data : dict
        User input data with possible empty values.

    Returns
    -------
    dict
        User data with defaults applied to empty fields.
    """
    # Validate input type.
    CheckType.is_dict(user_data)

    # Replace empty values with defaults.
    data = user_data.copy()
    default_values = get_default_values_that_may_be_used()
    for key, value in default_values.items():
        if data[key]["Value"] == "":
            data[key]["Value"] = value

    return data


# ------------------------------
# Data extraction functions
# ------------------------------
def extract_user_data_from_gui(entries: dict, repeat_value: str) -> dict:
    """Extract user input values from GUI entry widgets.

    Parameters
    ----------
    entries : dict
        Dictionary of GUI entries. Each value has keys
        'Use entry' (BooleanVar or None) and 'Entry'
        (tk.Entry widget).
    repeat_value : str
        The selected weekly repeat option.

    Returns
    -------
    dict
        Structured user data dictionary.
    """
    # Validate input types.
    CheckType.is_dict(entries)
    CheckType.is_str(repeat_value)

    # Build user data dictionary from GUI entries.
    user_data = {}
    user_data["Weekly repaet"] = {"Use value": True, "Value": repeat_value}
    for key, data in entries.items():
        # Some fields (Sidste dato, Sluttidspunkt) do not have a checkbox.
        use_value = data["Use entry"].get() if key not in ["Sidste dato", "Sluttidspunkt"] else None
        value = data["Entry"].get().strip()
        user_data[key] = {"Use value": use_value, "Value": value}

    return user_data


def convert_integer_fields(user_data: dict) -> dict:
    """Convert numeric string fields to integers.

    Converts fields whose keys contain "antal dage" or
    "antal timer" from string values to integer values.

    Parameters
    ----------
    user_data : dict
        User data with string values.

    Returns
    -------
    dict
        User data with integer conversions applied.
    """
    # Validate input type.
    CheckType.is_dict(user_data)

    # Convert fields containing "antal dage" or "antal timer".
    for key in user_data:
        if "antal dage" in key or "antal timer" in key:
            user_data[key]["Value"] = int(user_data[key]["Value"])

    return user_data


# ------------------------------
# Data conversion functions
# ------------------------------
def get_dates_in_range(
    first_date: datetime.date,
    last_date: datetime.date | None,
) -> list[datetime.date]:
    """Return all dates from first_date to last_date.

    Parameters
    ----------
    first_date : datetime.date
        The start date (inclusive).
    last_date : datetime.date | None
        The end date (inclusive). If None, returns only
        first_date.

    Returns
    -------
    list[datetime.date]
        List of dates in the range.
    """
    # Validate input types.
    CheckType.is_date(first_date)
    if last_date is not None:
        CheckType.is_date(last_date)

    # If no last date, return only the first date.
    if last_date is None:
        return [first_date]

    # Build list of all dates in range.
    all_dates = [first_date]
    current = first_date
    while current + datetime.timedelta(days=1) <= last_date:
        current = current + datetime.timedelta(days=1)
        all_dates.append(current)

    return all_dates


def filter_dates_by_weekday(
    dates: list[datetime.date],
    weekday: str,
) -> list[datetime.date]:
    """Filter dates to keep only those on a given weekday.

    Parameters
    ----------
    dates : list[datetime.date]
        List of dates to filter.
    weekday : str
        Danish weekday name (e.g. "Mandag"). Use
        "Ingen gentagelse" to keep all dates.

    Returns
    -------
    list[datetime.date]
        Filtered list of dates.
    """
    # Validate input types.
    CheckType.is_list(dates)
    CheckType.is_str(weekday)

    # If no repetition, keep all dates.
    if weekday == "Ingen gentagelse":
        return dates

    # Keep only dates matching the specified weekday.
    kept_dates = []
    for date in dates:
        danish_weekday = translate_weekday_from_english_to_danish(date.strftime("%A"))
        if weekday == danish_weekday:
            kept_dates.append(date)

    return kept_dates


def _parse_time_string(time_string: str) -> tuple[int, int]:
    """Parse a time string (HH:MM) into hours and minutes.

    Parameters
    ----------
    time_string : str
        Time in format "HH:MM".

    Returns
    -------
    tuple[int, int]
        Tuple of (hours, minutes).
    """
    # Validate input type.
    CheckType.is_str(time_string)

    # Split into hours and minutes.
    hour = int(time_string[0:2])
    minute = int(time_string[3:5])

    return hour, minute


def _calculate_optional_datetime(
    reference_time: datetime.datetime,
    user_data_entry: dict,
    delta_unit: str,
    add: bool = False,
) -> datetime.datetime | None:
    """Calculate an optional datetime offset from a reference.

    Parameters
    ----------
    reference_time : datetime.datetime
        The reference datetime to offset from.
    user_data_entry : dict
        Entry with 'Use value' and 'Value' keys.
    delta_unit : str
        Either "days" or "hours".
    add : bool
        If True, add offset. If False, subtract.

    Returns
    -------
    datetime.datetime | None
        The calculated datetime, or None if not used.
    """
    # Validate input types.
    CheckType.is_datetime(reference_time)
    CheckType.is_dict(user_data_entry)
    CheckType.is_str(delta_unit)
    CheckType.is_bool(add)

    # Return None if the field is not enabled.
    if not user_data_entry["Use value"]:
        return None

    # Validate types.
    offset = user_data_entry["Value"]
    CheckType.is_int(offset)

    # Calculate the time delta.
    if delta_unit == "days":
        delta = datetime.timedelta(days=offset)
    elif delta_unit == "hours":
        delta = datetime.timedelta(hours=offset)
    else:
        raise ValueError(f"Unknown delta_unit: {delta_unit}")

    # Apply offset (add or subtract).
    if add:
        new_time = reference_time + delta
    else:
        new_time = reference_time - delta

    return new_time


def build_event_dict(
    date: datetime.date,
    user_data: dict,
) -> dict[str, str | datetime.datetime | None]:
    """Build a single event dictionary for a given date.

    Parameters
    ----------
    date : datetime.date
        The date for the event.
    user_data : dict
        The full user data dictionary.

    Returns
    -------
    dict[str, str | datetime.datetime | None]
        Event dictionary with all fields.
    """
    # Validate input types.
    CheckType.is_date(date)
    CheckType.is_dict(user_data)

    # Parse start and end times.
    start_h, start_m = _parse_time_string(user_data["Starttidspunkt"]["Value"])
    end_h, end_m = _parse_time_string(user_data["Sluttidspunkt"]["Value"])

    # Create start and end datetimes.
    start_time = datetime.datetime(date.year, date.month, date.day, start_h, start_m)
    end_time = datetime.datetime(date.year, date.month, date.day, end_h, end_m)

    # Build the base event dictionary.
    event: dict[str, str | datetime.datetime | None] = {
        "Start time": start_time,
        "End time": end_time,
    }

    # Add optional text fields (None if checkbox is unchecked).
    optional_text_keys = [
        "Email",
        "Adgangskode",
        "Titel",
        "Sted",
        "Tekst",
        "Navn på gruppe",
        "Navn på skabelon",
        "Maks antal deltagere",
    ]
    for key in optional_text_keys:
        if user_data[key]["Use value"]:
            event[key] = user_data[key]["Value"]
        else:
            event[key] = None

    # Calculate optional datetime fields.
    event["Earliest sign-up"] = _calculate_optional_datetime(
        start_time,
        user_data["Tidligste tilmelding (antal dage før)"],
        delta_unit="days",
        add=False,
    )
    event["Latest sign-up"] = _calculate_optional_datetime(
        start_time,
        user_data["Seneste tilmelding (antal timer før)"],
        delta_unit="hours",
        add=False,
    )
    event["Latest sign-off"] = _calculate_optional_datetime(
        start_time,
        user_data["Seneste afmelding (antal timer før)"],
        delta_unit="hours",
        add=False,
    )
    event["Start showing participant list"] = _calculate_optional_datetime(
        start_time,
        user_data["Deltagerliste vist fra (antal dage før)"],
        delta_unit="days",
        add=False,
    )
    event["Stop showing participant list"] = _calculate_optional_datetime(
        end_time,
        user_data["Deltagerliste vist indtil (antal dage efter)"],
        delta_unit="days",
        add=True,
    )

    return event


def convert_userdata_into_list_of_events(
    user_data: dict,
) -> list[dict[str, str | datetime.datetime | None]]:
    """Convert user data into a list of event dictionaries.

    Each dictionary holds information about one event.
    If the event does not repeat, the list has length 1.

    Parameters
    ----------
    user_data : dict
        The processed user data dictionary.

    Returns
    -------
    list[dict[str, str | datetime.datetime | None]]
        List of event dictionaries.
    """
    # Validate input type.
    CheckType.is_dict(user_data)

    # Parse the first date.
    weekday = user_data["Weekly repaet"]["Value"]
    first_date = datetime.datetime.strptime(user_data["Første dato"]["Value"], "%d-%m-%Y").date()

    # Parse the last date (only if event repeats).
    if weekday != "Ingen gentagelse":
        last_date = datetime.datetime.strptime(user_data["Sidste dato"]["Value"], "%d-%m-%Y").date()
    else:
        last_date = None

    # Get all dates in the range.
    all_dates = get_dates_in_range(first_date, last_date)

    # Filter dates to match the selected weekday.
    kept_dates = filter_dates_by_weekday(all_dates, weekday)

    # Build an event dictionary for each kept date.
    events = []
    for date in kept_dates:
        event = build_event_dict(date, user_data)
        events.append(event)

    return events


# ------------------------------
# Merge stored inputs with fields
# ------------------------------
def merge_stored_inputs_with_fields(fields: dict) -> dict:
    """Merge stored user inputs with field definitions.

    Loads previously saved user inputs and updates the
    default values in the field definitions. Ensures
    that dates are not in the past.

    Parameters
    ----------
    fields : dict
        Field definitions from get_fields().

    Returns
    -------
    dict
        Updated field definitions with stored values.
    """
    # Validate input type.
    CheckType.is_dict(fields)

    # Load stored user inputs.
    stored_inputs = load_stored_user_inputs()
    if stored_inputs is None:
        return fields

    # Merge stored values into field definitions.
    try:
        for key in stored_inputs.keys():
            if key in fields.keys():
                parsed = ast.literal_eval(stored_inputs[key])
                fields[key][0] = parsed["Use value"]
                fields[key][1] = parsed["Value"]
    except Exception:
        pass

    # Ensure dates are not in the past.
    today = datetime.datetime.now().date()
    for key in ["Første dato", "Sidste dato"]:
        if fields[key][1] != "":
            try:
                date = datetime.datetime.strptime(fields[key][1], "%d-%m-%Y").date()
                if date < today:
                    fields[key][1] = today.strftime("%d-%m-%Y")
            except ValueError:
                pass

    return fields


# ------------------------------
# Validation helper functions
# ------------------------------
def _validate_required_fields_enabled(data_raw: dict) -> str | None:
    """Check that all required fields are enabled.

    Parameters
    ----------
    data_raw : dict
        Raw user data with 'Use value' flags.

    Returns
    -------
    str | None
        Error message, or None if all required fields
        are enabled.
    """
    # Validate input type.
    CheckType.is_dict(data_raw)

    # Define required fields with their display names.
    required_fields = {
        "Email": "Email",
        "Adgangskode": "Adgangskode",
        "Navn på gruppe": "Navn på gruppe",
        "Navn på skabelon": "Navn på skabelon",
        "Første dato": "Dato(er)",
        "Starttidspunkt": "Tidspunkt",
        "Titel": "Titel",
    }

    # Check each required field.
    for field_name, display_name in required_fields.items():
        if not data_raw[field_name]["Use value"]:
            return f"Du må ikke deaktivere feltet: {display_name}"

    return None


def _validate_credentials(data: dict) -> str | None:
    """Validate email and password fields.

    Parameters
    ----------
    data : dict
        Dictionary with field values.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Validate email and password.
    if data["Email"] == "":
        return "Ugyldig email."
    if "@" not in data["Email"]:
        return "Ugyldig email."
    if data["Adgangskode"] == "":
        return "Ugyldig adgangskode."

    return None


def _validate_group_and_template(data: dict) -> str | None:
    """Validate group and template names.

    Parameters
    ----------
    data : dict
        Dictionary with field values.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Validate group and template names.
    if data["Navn på gruppe"] == "":
        return "Ugyldigt gruppenavn"
    if data["Navn på skabelon"] == "":
        return "Ugyldigt skabelonnavn"

    return None


def _validate_repeat_settings(data: dict) -> str | None:
    """Validate weekly repeat vs. end date consistency.

    Parameters
    ----------
    data : dict
        Dictionary with field values.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Validate repeat settings
    no_repeat = data["Weekly repaet"] == "Ingen gentagelse"
    if no_repeat and data["Sidste dato"] != "":
        return "Eftersom arrangementet ikke gentages, skal du ikke indtaste en slutdato."
    if not no_repeat and data["Sidste dato"] == "":
        return "Eftersom arrangementet gentages, skal du indtaste en slutdato."

    return None


def _validate_dates(
    data: dict,
    confirm: Callable[[str, str], bool] | None = None,
) -> str | None:
    """Validate first and last dates.

    Parameters
    ----------
    data : dict
        Dictionary with field values.
    confirm : Callable | None
        Callback for user confirmations. Called with
        (title, message), returns True to proceed.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Validate first date format.
    if len(data["Første dato"]) != 10:
        return "Ugyldig startdato."

    # Parse and validate first date.
    try:
        first_date = datetime.datetime.strptime(data["Første dato"], "%d-%m-%Y").date()
    except ValueError:
        return "Ugyldig startdato."

    # Check that start date is not in the past.
    today = datetime.datetime.now().date()
    if first_date < today:
        return "Startdatoen kan ikke være i fortiden."

    # Warn if start date is far in the future.
    if first_date > today + datetime.timedelta(days=30):
        if confirm is not None:
            message = "Startdatoen er langt ude i fremtiden. Er dette bevidst?"
            if not confirm("Mærkligt input", message):
                return "Forkert indtastet startdato."

    # Validate last date format.
    if len(data["Sidste dato"]) not in [0, 10]:
        return "Ugyldig slutdato."

    # Parse and validate last date (if provided).
    if len(data["Sidste dato"]) == 10:
        try:
            last_date = datetime.datetime.strptime(data["Sidste dato"], "%d-%m-%Y").date()
        except ValueError:
            return "Ugyldig slutdato."

        # Last date must be after first date.
        if last_date <= first_date:
            return "Slutdatoen skal være efter startdatoen."

        # Warn if event spans many months.
        if last_date > first_date + datetime.timedelta(days=7 * 10):
            if confirm is not None:
                message = "Arrangementet strækker sig over mange måneder. Er dette bevidst?"
                if not confirm("Mærkligt input", message):
                    return "Forkert indtastet datoer."

    return None


def _is_valid_time_format(value: str) -> bool:
    """Check if a string is a valid time in HH:MM format.

    Parameters
    ----------
    value : str
        The time string to validate.

    Returns
    -------
    bool
        True if the format is valid.
    """
    # Validate input type.
    CheckType.is_str(value)

    # Check format: length, colon, digits, ranges.
    if len(value) != 5:
        return False
    if value[2] != ":":
        return False
    if not value[0:2].isdigit() or not value[3:5].isdigit():
        return False
    if int(value[0:2]) >= 24 or int(value[3:5]) >= 60:
        return False

    return True


def _calculate_duration_hours(start_time: str, end_time: str) -> float:
    """Calculate event duration in hours from time strings.

    Parameters
    ----------
    start_time : str
        Start time in "HH:MM" format.
    end_time : str
        End time in "HH:MM" format.

    Returns
    -------
    float
        Duration in hours.
    """
    # Validate input types.
    CheckType.is_str(start_time)
    CheckType.is_str(end_time)

    # Convert to minutes and calculate duration.
    start_minutes = 60 * int(start_time[0:2]) + int(start_time[3:5])
    end_minutes = 60 * int(end_time[0:2]) + int(end_time[3:5])
    duration_hours = (end_minutes - start_minutes) / 60

    return duration_hours


def _validate_times(
    data: dict,
    confirm: Callable[[str, str], bool] | None = None,
) -> str | None:
    """Validate start and end times.

    Parameters
    ----------
    data : dict
        Dictionary with field values.
    confirm : Callable | None
        Callback for user confirmations.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Validate time format for both start and end.
    for key in ["Starttidspunkt", "Sluttidspunkt"]:
        if not _is_valid_time_format(data[key]):
            return f"Ugyldig {key.lower()}."

    # Calculate duration.
    duration_hours = _calculate_duration_hours(data["Starttidspunkt"], data["Sluttidspunkt"])

    # Check that end is after start.
    if duration_hours < 0:
        return "Ugyldigt klokkeslæt. Starttidspunktet skal være før sluttidspunktet."

    # Warn about very short events.
    if duration_hours < 0.5 and confirm is not None:
        message = "Arrangementet varer under en halv time. Er dette bevidst?"
        if not confirm("Mærkligt input", message):
            return "Forkert indtastet klokkeslæt."

    # Warn about very long events.
    if duration_hours > 3 and confirm is not None:
        message = f"Arrangementet varer {duration_hours} timer. Er dette bevidst?"
        if not confirm("Mærkligt input", message):
            return "Forkert indtastet klokkeslæt."

    return None


def _validate_start_not_in_past(data: dict) -> str | None:
    """Validate that the event start is not in the past.

    Parameters
    ----------
    data : dict
        Dictionary with field values.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Parse first date and start time.
    first_date = datetime.datetime.strptime(data["Første dato"], "%d-%m-%Y").date()
    start_time = datetime.datetime(
        first_date.year,
        first_date.month,
        first_date.day,
        int(data["Starttidspunkt"][0:2]),
        int(data["Starttidspunkt"][3:5]),
    )

    # Check against current time.
    if start_time < datetime.datetime.now():
        return "Starttidspunktet kan ikke være i fortiden."

    return None


def _validate_title(data: dict) -> str | None:
    """Validate the event title.

    Parameters
    ----------
    data : dict
        Dictionary with field values.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Validate title length
    title = data["Titel"]
    if len(title) == 0:
        return "Indtast en titel."
    if len(title) > 100:
        return f"Titlen er for lang. Den er på {len(title)} tegn, " f"men må maksimalt være 100 tegn."

    return None


def _validate_location_and_description(data: dict) -> str | None:
    """Validate location and description text lengths.

    Parameters
    ----------
    data : dict
        Dictionary with field values.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Validate length of text.
    len_loc = len(data["Sted"])
    len_text = len(data["Tekst"])
    if len_loc > 10000:
        return f"Stedet er for langt. Den er på {len_loc} tegn, " f"men må maksimalt være 10.000 tegn."
    if len_text > 10000:
        return f"Den beskrivende tekst er for langt. Den er på " f"{len_text} tegn, men må maksimalt være 10.000 tegn."

    return None


def _validate_max_participants(data: dict) -> str | None:
    """Validate maximum number of participants.

    Parameters
    ----------
    data : dict
        Dictionary with field values.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Validate input type.
    CheckType.is_dict(data)

    # Validate maximum number of participants.
    default_values = get_default_values_that_may_be_used()
    max_participants = data["Maks antal deltagere"]
    if max_participants == "":
        max_participants = default_values["Maks antal deltagere"]
    if not max_participants.isdigit():
        return "Ugyldigt antal deltagere."
    if int(max_participants) > 1000:
        return "Du maksimale antal deltagere kan højst være 1.000."

    return None


def _validate_signup_times(data: dict) -> str | None:
    """Validate sign-up and sign-off time settings.

    Parameters
    ----------
    data : dict
        Dictionary with field values.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """

    # Validate input type.
    CheckType.is_dict(data)

    # Get values (use defaults if empty).
    default_values = get_default_values_that_may_be_used()
    earliest_signup = data["Tidligste tilmelding (antal dage før)"]
    latest_signup = data["Seneste tilmelding (antal timer før)"]
    latest_signoff = data["Seneste afmelding (antal timer før)"]
    if earliest_signup == "":
        earliest_signup = default_values["Tidligste tilmelding (antal dage før)"]
    if latest_signup == "":
        latest_signup = default_values["Seneste tilmelding (antal timer før)"]
    if latest_signoff == "":
        latest_signoff = default_values["Seneste afmelding (antal timer før)"]

    # Validate earliest sign-up.
    if not earliest_signup.isdigit():
        return "Ugyldig tidligste tilmelding. Indtast antal dage før arrangementets start."
    if int(earliest_signup) > 365:
        return "Den tidligste tilmelding må maksimalt være et år før arrangementet starter."

    # Validate latest sign-up.
    if not latest_signup.isdigit():
        return (
            "Ugyldigt seneste tilmelding (deadline for tilmelding). " "Indtast antal timer før arrangementets start."
        )
    if int(latest_signup) > 4 * 7 * 24:
        return (
            "Den seneste tilmelding (deadline for tilmelding) kan tidligst " "være fire uger før arrangementets start."
        )

    # Earliest sign-up (days) must be before latest sign-up (hours).
    if int(earliest_signup) * 24 < int(latest_signup):
        return (
            "Tidligst mulige tilmelding (antal dage før) skal være " "før senest mulige tilmelding (antal timer før)."
        )

    # Validate latest sign-off.
    if not latest_signoff.isdigit():
        return (
            "Den seneste afmelding skal være antal timer før " "arrangementets start, hvor man senest kan afmelde sig."
        )

    # Latest sign-up must be before (or same as) latest sign-off.
    if int(latest_signoff) > int(latest_signup):
        return "Den seneste tilmelding skal være før (eller samtidig " "med) seneste afmelding."

    return None


def _validate_participant_list(data: dict) -> str | None:
    """Validate participant list display settings.

    Parameters
    ----------
    data : dict
        Dictionary with field values.

    Returns
    -------
    str | None
        Error message, or None if valid.
    """
    # Validate input type.
    CheckType.is_dict(data)

    # Extract values (use defaults if empty).
    default_values = get_default_values_that_may_be_used()
    earliest_part = data["Deltagerliste vist fra (antal dage før)"]
    latest_part = data["Deltagerliste vist indtil (antal dage efter)"]
    earliest_signup = data["Tidligste tilmelding (antal dage før)"]
    if earliest_signup == "":
        earliest_signup = default_values["Tidligste tilmelding (antal dage før)"]

    # Calculate duration for comparison.
    duration_hours = _calculate_duration_hours(data["Starttidspunkt"], data["Sluttidspunkt"])

    # Validate earliest participant list date.
    if earliest_part != "" and not earliest_part.isdigit():
        return "Ugyldigt antal dage som deltagerlisten vises fra."

    # Validate latest participant list date.
    if latest_part != "" and not latest_part.isdigit():
        return "Ugyldigt antal dage som deltagerlisten vises indtil."

    # Check ordering constraints (using int comparison to avoid string comparison bugs).
    if earliest_part != "" and int(earliest_part) > int(earliest_signup):
        return "Deltagerlisten kan tidligst vises samme tid som tilmeldingen åbnes."
    if latest_part != "" and int(latest_part) < duration_hours / 24:
        return "Du kan ikke stoppe med at vise deltagerlisten før arrangementet er afsluttet."
    if latest_part != "" and int(latest_part) > 3 * 365:
        return "Du kan senest stoppe med at vise deltagerlisten tre år efter arrangementet er afsluttet."

    return None


# ------------------------------
# Docker
# ------------------------------
def is_running_in_docker() -> bool:
    """Check if the application is running inside a Docker container.

    Returns
    -------
    bool
        True if running in Docker, False otherwise.
    """

    # Method 1: Check for Docker environment file.
    running_in_docker = False
    if os.path.exists("/.dockerenv"):
        running_in_docker = True

    # Method 2: Check cgroup info
    try:
        with open("/proc/1/cgroup", "rt") as f:
            if "docker" in f.read() or "containerd" in f.read():
                running_in_docker = True
    except FileNotFoundError:
        pass

    return running_in_docker


# ------------------------------
# Main validation function
# ------------------------------
def validate_user_data(
    data_raw: dict,
    confirm: Callable[[str, str], bool] | None = None,
) -> str:
    """Validate all user data fields.

    Runs all validation checks in order. Returns "Valid"
    if all checks pass, or an error message string on
    the first failure.

    Parameters
    ----------
    data_raw : dict
        Raw user data with 'Use value' and 'Value' keys.
    confirm : Callable | None
        Callback for user confirmations (e.g.
        messagebox.askyesno). Called with (title, message),
        returns True to proceed.

    Returns
    -------
    str
        "Valid" if all data is valid, or an error message.
    """
    # Validate input type.
    CheckType.is_dict(data_raw)

    # Check that required fields are enabled.
    error = _validate_required_fields_enabled(data_raw)
    if error is not None:
        return error

    # Extract just the values for convenience.
    data = {}
    for key in data_raw.keys():
        data[key] = data_raw[key]["Value"]

    # Run all validators in order.
    error = _validate_credentials(data)
    if error is not None:
        return error

    error = _validate_group_and_template(data)
    if error is not None:
        return error

    error = _validate_repeat_settings(data)
    if error is not None:
        return error

    error = _validate_dates(data, confirm)
    if error is not None:
        return error

    error = _validate_times(data, confirm)
    if error is not None:
        return error

    error = _validate_start_not_in_past(data)
    if error is not None:
        return error

    error = _validate_title(data)
    if error is not None:
        return error

    error = _validate_location_and_description(data)
    if error is not None:
        return error

    error = _validate_max_participants(data)
    if error is not None:
        return error

    error = _validate_signup_times(data)
    if error is not None:
        return error

    error = _validate_participant_list(data)
    if error is not None:
        return error

    return "Valid"
