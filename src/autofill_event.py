# ------------------------------
# Selenium automation for Membersite
# ------------------------------
# This module automates the creation of events on the
# Membersite website using Selenium WebDriver.
#
# Author: Jonas Groenkjaer Pedersen
# ------------------------------


# ------------------------------
# Packages
# ------------------------------
import datetime
import time
import shutil

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver  # Only used for type hints.
from typing import Callable

from backend import is_running_in_docker
from utils import CheckType


# ------------------------------
# Custom exception
# ------------------------------
class EventCreationError(Exception):
    """Raised when an event creation step fails."""

    pass


# ------------------------------
# Low-level Selenium helpers
# ------------------------------
def _get_active_element(driver: WebDriver) -> WebElement:
    """Return the currently focused element in the browser.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.

    Returns
    -------
    WebElement
        The currently active/focused element.
    """
    # Validate input type.
    CheckType._check_type(driver, WebDriver)

    return driver.switch_to.active_element


def _find_element(
    driver: WebDriver,
    by: str,
    value: str,
    timeout: int = 10,
) -> WebElement:
    """Find an element on the webpage with a wait timeout.

    Unlike driver.find_element(), this function waits up
    to ``timeout`` seconds for the element to appear,
    preventing crashes when the page has not loaded yet.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    by : str
        The locator strategy (e.g. "name", "id",
        "xpath").
    value : str
        The locator value.
    timeout : int
        Maximum seconds to wait for the element.

    Returns
    -------
    WebElement
        The found element.
    """
    # Wait for the element to be present in the DOM.
    wait = WebDriverWait(driver, timeout)
    element = wait.until(expected_conditions.presence_of_element_located((by, value)))

    return element


def _find_clickable_element(
    driver: WebDriver,
    by: str,
    value: str,
    timeout: int = 10,
) -> WebElement:
    """Find a clickable element on the webpage with a wait timeout.

    Unlike driver.find_element(), this function waits up
    to ``timeout`` seconds for the element to be clickable,
    preventing crashes when the page has not loaded yet.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    by : str
        The locator strategy (e.g. "name", "id",
        "xpath").
    value : str
        The locator value.
    timeout : int
        Maximum seconds to wait for the element.

    Returns
    -------
    WebElement
        The found element.
    """
    # Wait for the element to be clickable.
    wait = WebDriverWait(driver, timeout)
    element = wait.until(expected_conditions.element_to_be_clickable((by, value)))

    return element


def _extract_linked_id_from_label(
    driver: WebDriver,
    displayed_label_name: str,
) -> str | None:
    """Return the ID that a label's 'for' attribute links to.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    displayed_label_name : str
        The visible text of the label.

    Returns
    -------
    str | None
        The value of the label's 'for' attribute.
    """
    # Validate input type.
    CheckType.is_str(displayed_label_name)

    # Find the label by its text content.
    label = _find_element(
        driver,
        "xpath",
        f"//label[contains(., '{displayed_label_name}')]",
    )
    id_that_label_is_linked_to = label.get_attribute("for")

    return id_that_label_is_linked_to


def _enter_datetime_into_field(
    element: WebElement,
    dtime: datetime.datetime,
    date_format: str = "%Y-%m-%d",
    time_format: str | None = "%H:%M",
) -> None:
    """Enter a datetime value into a date-time input field.

    Types the date, presses Tab, then types the time.

    Parameters
    ----------
    element : WebElement
        The input element to type into.
    dtime : datetime.datetime
        The datetime value to enter.
    """
    # Validate input type.
    CheckType.is_datetime(dtime)

    # If the input is a `datetime-local`, set the combined value (YYYY-MM-DDTHH:MM).
    input_type = element.get_attribute("type") or ""
    if input_type.lower() == "datetime-local":
        value = dtime.strftime("%Y-%m-%dT%H:%M")
        # Prefer setting via JS for reliability, fall back to send_keys.
        try:
            script = (
                "arguments[0].value = arguments[1]; "
                + "arguments[0].dispatchEvent(new Event('input')); "
                + "arguments[0].dispatchEvent(new Event('change'));"
            )
            driver = element.parent
            driver.execute_script(script, element, value)
        except Exception:
            element.send_keys(value)
        return None

    # Default behaviour: enter date, tab to time field, enter time.
    element.send_keys(dtime.strftime(date_format))
    element.send_keys(Keys.TAB)
    if time_format is not None:
        element.send_keys(dtime.strftime(time_format))

    return None


def _initialize_driver(on_driver_created: Callable[[WebDriver], None] | None = None) -> WebDriver:
    """Create and configure a Chrome WebDriver instance.

    Parameters
    ----------
    on_driver_created : callable | None
        Optional callback function to be called when the driver is created.

    Returns
    -------
    WebDriver
        A maximized Chrome browser at 80% zoom.
    """

    # Determine if the code is running inside a Docker container.
    is_docker = is_running_in_docker()

    # Raise error if Chromium and Chromedriver are not available.
    if is_docker:
        chromium_path, chromedriver_path = get_paths_of_chronium_and_chromedriver()

    # Intialize options variable. The main purpose is to specify that Chrome must be zoomed outout.
    # If any elements are not visible on the screen (and scrolling is required to see them), then Selenium
    # cannot interact with the elements. By zooming out, more elements fit on the screen and become interactable.
    options = Options()

    # Options if running on laptop.
    if not is_docker:
        options.add_argument("--start-maximized")  # Maximize window.
        options.add_argument("--force-device-scale-factor=0.8")  # 80% zoom.

    # Options if running inside Docker.
    if is_docker:
        options.add_argument("--window-size=3840,2160")  # Window size.
        options.add_argument("--headless=new")  # Run in headless mode => No visible window (required for Docker).
        options.add_argument("--disable-gpu")  # Disable GPU for better compatibility in headless mode.
        options.add_argument("--no-sandbox")  # Required for Docker.
        options.add_argument("--disable-dev-shm-usage")  # To prevent crashes in Docker due to limited memory size.
        options.add_argument("--single-process")  # To prevent Render from crashing due to restrained resources.
        options.add_argument("--disable-dev-tools")  # Disable DevTools to save resources.
        options.add_argument("--no-zygote")  # Disable zygote process for better compatibility in Docker.
        options.binary_location = chromium_path  # Specify Chromium path for Docker.  # type: ignore
        service = Service(chromedriver_path)  # Specify chromedriver path for Docker.  # type: ignore

    # Options which improves the start up time.
    options.add_argument("--disable-extensions")  # Disable extensions.
    options.add_argument("--no-first-run")  # Skip first-run setup.
    options.add_argument("--no-default-browser-check")  # Skip default browser check.

    # Create the driver.
    try:
        if not is_docker:
            driver = webdriver.Chrome(options=options)  # pyright: ignore
        else:
            driver = webdriver.Chrome(options=options, service=service)  # pyright: ignore
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise

    # Notify caller that a driver was created (if callback provided).
    if on_driver_created is not None:
        try:
            on_driver_created(driver)
        except Exception:
            pass  # Do not fail the whole flow if callback raises.

    return driver


def get_paths_of_chronium_and_chromedriver() -> tuple[str, str] | tuple[None, None]:
    """Return the paths of Chromium and Chromedriver in a Docker environment.

    If the script was not executed inside Docker, None is returned.

    Returns
    ----------
    chromium_path : str | None
        The file path to the Chromium executable.
    chromedriver_path : str | None
        The file path to the Chromedriver executable.

    Raises
    ------
    EventCreationError
        If either Chromium or Chromedriver is not found.
    """

    # Stop if this is not a Docker environment.
    is_docker = is_running_in_docker()
    if not is_docker:
        return (None, None)

    # Get paths.
    chromium_path = shutil.which("chromium")
    if chromium_path is None:
        chromium_path = shutil.which("chromium-browser")
    chromedriver_path = shutil.which("chromedriver")

    # Raise errors if not found.
    if chromium_path is None:
        raise EventCreationError("Failed to locate Chromium. Is it installed?")
    if chromedriver_path is None:
        raise EventCreationError("Failed to locate Chromedriver. Is it installed?")

    # Debug prints.
    print("Chromium path:", chromium_path)
    print("Chromedriver path:", chromedriver_path)

    return chromium_path, chromedriver_path


# ------------------------------
# Step functions (each step of event creation)
# ------------------------------
def _open_webpage(driver: WebDriver) -> None:
    """Navigate to the Membersite event creation page.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    """
    webpage = "https://danskestudentersroklub-groups.membersite.dk/Events/CreateEvent"
    driver.get(webpage)

    return None


def _login(driver: WebDriver, data: dict) -> None:
    """Log in to Membersite with email and password.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    data : dict
        Event data containing 'Email' and 'Adgangskode'.

    Raises
    ------
    EventCreationError
        If login fails.
    """
    # Validate input type.
    CheckType.is_dict(data)

    try:
        # Enter email.
        username = _find_element(driver, by="name", value="Username")
        username.send_keys(data["Email"])

        # Enter password.
        password = _find_element(driver, by="name", value="Password")
        password.send_keys(data["Adgangskode"])

        # Click the "Login" button.
        button = _find_clickable_element(driver, by="id", value="login-submit-btn")
        button.click()

        # Verify login succeeded by checking for the "Netværk" field.
        group_id = _extract_linked_id_from_label(driver, displayed_label_name="Netværk")
        if group_id is None:
            raise EventCreationError("Could not find the Netværk field.")
        _find_element(driver, by="name", value=group_id, timeout=2)
    except Exception:
        raise EventCreationError("Kunne ikke logge ind. Er din e-mail og adgangskode korrekt?")

    return None


def _select_group(driver: WebDriver, data: dict) -> None:
    """Select the group/network for the event.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    data : dict
        Event data containing 'Navn på gruppe'.

    Raises
    ------
    EventCreationError
        If the group cannot be selected.
    """
    # Validate input type.
    CheckType.is_dict(data)

    try:
        # Open the dropdown menu for group selection.
        group_label = _find_element(
            driver,
            "xpath",
            "//label[@class='floating-form-label' and text()='Netværk']",
        )
        group_label_id = group_label.get_attribute("for")
        if group_label_id is None:
            raise EventCreationError("Could not find the group dropdown.")
        group_dropdown = _find_clickable_element(driver, "id", group_label_id)
        group_dropdown.click()

        # Select the desired group from the dropdown.
        time.sleep(0.2)  # Wait for dropdown animation.
        group_name = data["Navn på gruppe"]
        label = _find_clickable_element(driver, "xpath", f"//li[normalize-space()='{group_name}']")
        label.click()
    except Exception:
        raise EventCreationError(
            f'Kunne ikke vælge gruppen "{data["Navn på gruppe"]}". ' "Er du administrator af gruppen?"
        )

    return None


def _select_template(driver: WebDriver, data: dict) -> None:
    """Select the event template.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    data : dict
        Event data containing 'Navn på skabelon'.

    Raises
    ------
    EventCreationError
        If the template cannot be selected.
    """
    # Validate input type.
    CheckType.is_dict(data)

    try:
        # Click "Skabelon" to use a template (not a copy of previous event).
        label_1 = _find_clickable_element(
            driver,
            "xpath",
            "//label[@class='form-check-label ms-2' and text()='Skabelon']",
        )
        label_1.click()

        # Open the template dropdown.
        label_2 = _find_element(
            driver,
            "xpath",
            "//label[@class='floating-form-label' and text()='Skabelon']",
        )
        label_2_id = label_2.get_attribute("for")
        if label_2_id is None:
            raise EventCreationError("Could not find the template dropdown.")
        label_3 = _find_clickable_element(driver, "id", label_2_id)
        label_3.click()

        # Select the desired template from the dropdown.
        time.sleep(0.2)  # Wait for dropdown animation.
        template_name = data["Navn på skabelon"]
        label_4 = _find_clickable_element(driver, "xpath", f"//li[normalize-space()='{template_name}']")
        label_4.click()

        # Press "Næste" (Next) to proceed.
        time.sleep(0.2)  # Wait for selection to register.
        button_xpath = "//button[contains(@class,'btn-primary') and normalize-space()='Næste']"
        next_button = _find_clickable_element(driver, "xpath", button_xpath)
        next_button.click()
    except Exception:
        raise EventCreationError(
            f'Kunne ikke vælge skabelonen "{data["Navn på skabelon"]}". ' "Er skabelonen stavet korrekt?"
        )

    return None


def _enter_basic_info(driver: WebDriver, data: dict) -> None:
    """Enter title and max participants.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    data : dict
        Event data with 'Titel' and optionally
        'Maks antal deltagere'.

    Raises
    ------
    EventCreationError
        If basic info cannot be entered.
    """
    # Enter title.
    try:
        time.sleep(1)  # Wait for the page to load.
        title = _find_element(driver, by="name", value="ComponentModel.ArrangementName")
        title.send_keys(100 * Keys.BACKSPACE)  # Clear existing text.
        title.send_keys(data["Titel"])
    except Exception:
        raise EventCreationError("Kunne ikke indsætte titlen. Er der fejl i titlen?")

    # Enter max participants (if provided).
    if data["Maks antal deltagere"] is not None:
        try:
            max_part = _find_element(driver, by="name", value="ComponentModel.MaxParticipants")
            max_part.send_keys(10 * Keys.BACKSPACE)  # Clear existing value.
            max_part.send_keys(data["Maks antal deltagere"])
        except Exception:
            raise EventCreationError("Kunne ikke indsætte deltagerbegrænsningen.")

    return None


def _enter_time_fields(driver: WebDriver, data: dict) -> None:
    """Enter all time-related fields.

    Fills in start time, end time, earliest sign-up,
    latest sign-up, latest sign-off, and participant
    list display dates.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    data : dict
        Event data with datetime values.

    Raises
    ------
    EventCreationError
        If any time field cannot be entered.
    """

    # Define the time fields to fill in: (data_key, html_name, error_message).
    time_fields = [
        ("Start time", "ComponentModel.StartDateTime", "Kunne ikke indsætte starttidspunktet."),
        ("End time", "ComponentModel.EndDateTime", "Kunne ikke indsætte sluttidspunktet."),
        (
            "Earliest sign-up",
            "ComponentModel.EarliestEnrollDateTime",
            "Kunne ikke indsætte tidligste tilmeldingstidspunkt.",
        ),
        ("Latest sign-up", "ComponentModel.EnrollBeforeDateTime", "Kunne ikke indsætte seneste tilmeldingstidspunkt."),
        ("Latest sign-off", "ComponentModel.CancelSignupDateTime", "Kunne ikke indsætte seneste afmeldingstidspunkt."),
        (
            "Start showing participant list",
            "ComponentModel.EarliestParticipantListViewDateTime",
            "Kunne ikke indsætte hvornår deltagerlisten må vises fra.",
        ),
        (
            "Stop showing participant list",
            "ComponentModel.LastParticipantListViewDateTime",
            "Kunne ikke indsætte hvornår deltagerlisten må vises til.",
        ),
    ]

    # Fill in each time field (skip if value is None).
    for data_key, html_name, error_msg in time_fields:
        if data[data_key] is not None:
            try:
                element = _find_element(driver, by="name", value=html_name)
                _enter_datetime_into_field(element, data[data_key], date_format="%Y-%m-%d", time_format="%H:%M")
            except Exception:
                raise EventCreationError(error_msg)

    return None


def _enter_location(driver: WebDriver, data: dict) -> None:
    """Enter the event location.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    data : dict
        Event data with optional 'Sted'.

    Raises
    ------
    EventCreationError
        If the location cannot be entered.
    """
    if data["Sted"] is None:
        return None

    try:
        location = _find_element(driver, by="name", value="ComponentModel.LocationText")
        # Select all existing text and replace it.
        location.send_keys(Keys.CONTROL + "a")
        location.send_keys(Keys.BACKSPACE)
        location.send_keys(data["Sted"])
    except Exception:
        raise EventCreationError("Kunne ikke indsætte lokationen.")

    return None


def _click_next_basic_info(driver: WebDriver) -> None:
    """Click the 'Next' button after basic info.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.

    Raises
    ------
    EventCreationError
        If the button cannot be clicked.
    """

    try:
        button_next = _find_clickable_element(driver, by="id", value="basic-info-next-or-save-button")
    except Exception:
        raise EventCreationError(
            "Kunne ikke finde 'Næste' knappen for basisoplysninger (navn, tid, sted osv.) på MemberSite."
        )

    try:
        button_next.click()
    except Exception:
        raise EventCreationError(
            "Kunne ikke klikke på 'Næste' knappen for basisoplysninger (navn, tid, sted osv.) på MemberSite. "
            + "Knappen findes, men kunne ikke trykkes på. Er der en fejl i de indtastede oplysninger?"
        )

    return None


def _enter_description(driver: WebDriver, data: dict) -> None:
    """Enter the event description text.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    data : dict
        Event data with optional 'Tekst'.

    Raises
    ------
    EventCreationError
        If the description cannot be entered.
    """
    if data["Tekst"] is None:
        return None

    try:
        time.sleep(0.5)  # Wait for the page to load.

        # Find the "Kort beskrivelse" label and navigate to the text box.
        label_text = "//*[text()='Kort beskrivelse']"
        label = _find_clickable_element(driver, by="xpath", value=label_text)
        label.click()
        label.send_keys(20 * Keys.TAB)  # Tab to the text box.

        # Enter the description text.
        textbox = _get_active_element(driver)
        textbox.click()
        textbox.send_keys(Keys.CONTROL + "a")  # Select all existing text.
        textbox.send_keys(Keys.BACKSPACE)  # Delete existing text.
        textbox.send_keys(data["Tekst"])

        # Navigate to and click the "Næste" (Next) button.
        label.click()
        label.send_keys(2 * Keys.TAB)
        button_next = _get_active_element(driver)
        button_next.click()
        time.sleep(0.5)  # Wait for navigation.
    except Exception:
        raise EventCreationError("Kunne ikke indtaste den ønskede tekst.")

    return None


def _save_event(driver: WebDriver) -> None:
    """Click the 'Save' button to finalize the event.

    Parameters
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.

    Raises
    ------
    EventCreationError
        If the event cannot be saved.
    """

    try:
        time.sleep(1)  # Wait for the page to load.
        save_button = _find_clickable_element(
            driver,
            by="id",
            value="participant-category-and-regular-service-next-button",
        )
    except Exception:
        raise EventCreationError("Kunne ikke finde 'Gem' knappen på MemberSite.")

    try:
        1 / 0  # Debug line to test screenshot capture.
        save_button.click()
    except Exception:
        raise EventCreationError(
            "Kunne ikke klikke på 'Gem' knappen på MemberSite. Knappen findes, men kunne ikke trykkes på. "
            + "Er der en fejl i de indtastede oplysninger?"
        )

    return None


# ------------------------------
# Main event creation function
# ------------------------------
def create_single_event(
    data: dict,
    driver: WebDriver | None = None,
    already_logged_in: bool = False,
    on_driver_created: Callable[[WebDriver], None] | None = None,
) -> tuple[WebDriver | None, str]:
    """Create a single event on MemberSite.

    Automates browser interaction to create one event.
    If driver is None, a new browser is opened. If
    already_logged_in is True, the login step is skipped.

    Parameters
    ----------
    data : dict
        Event data dictionary with all fields.
    driver : WebDriver | None
        Existing WebDriver instance, or None to create
        a new one.
    already_logged_in : bool
        Whether the user is already logged in.

    Returns
    -------
    tuple[WebDriver | None, str]
        The WebDriver instance and a status string
        ("Succes" or an error message).
    """
    # Validate input types.
    CheckType.is_dict(data)
    CheckType.is_bool(already_logged_in)

    # Initialize browser driver.
    if driver is None:
        try:
            driver = _initialize_driver()
        except Exception as e:
            return driver, f"Der er noget galt med programmet. Kontakt Jonas. Modtog følgende fejl: {e}"

    # Run all event creation steps in sequence.
    try:
        _open_webpage(driver)
    except Exception:
        return driver, "Kunne ikke åbne hjemmesiden. Har du internet?"

    try:
        if not already_logged_in:
            _login(driver, data)
    except EventCreationError as e:
        return driver, str(e)

    try:
        time.sleep(1)  # Wait for the page to load.
        _select_group(driver, data)
    except EventCreationError as e:
        return driver, str(e)

    try:
        _select_template(driver, data)
    except EventCreationError as e:
        return driver, str(e)

    try:
        _enter_basic_info(driver, data)
    except EventCreationError as e:
        return driver, str(e)

    try:
        _enter_time_fields(driver, data)
    except EventCreationError as e:
        return driver, str(e)

    try:
        _enter_location(driver, data)
    except EventCreationError as e:
        return driver, str(e)

    try:
        _click_next_basic_info(driver)
    except EventCreationError as e:
        return driver, str(e)

    try:
        _enter_description(driver, data)
    except EventCreationError as e:
        return driver, str(e)

    try:
        _save_event(driver)
    except EventCreationError as e:
        return driver, str(e)

    return driver, "Succes"


# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    my_event = {
        "Email": "mit.navn@email.com",
        "Adgangskode": "MinAdgangskode123",
        "Navn på gruppe": "Min Gruppe",
        "Navn på skabelon": "Min Skabelon",
        "Titel": "Tester",
        "Maks antal deltagere": 1,
        "Start time": datetime.datetime(2027, 1, 1, 18, 0),
        "End time": datetime.datetime(2027, 1, 1, 20, 0),
        "Earliest sign-up": datetime.datetime(2027, 1, 1, 0, 0),
        "Latest sign-up": datetime.datetime(2027, 1, 1, 12, 0),
        "Latest sign-off": datetime.datetime(2027, 1, 1, 12, 0),
        "Start showing participant list": datetime.datetime(2027, 1, 1, 0, 0),
        "Stop showing participant list": datetime.datetime(2027, 1, 1, 20, 0),
        "Sted": "Min Lokation",
        "Tekst": None,
    }

    driver, status = create_single_event(my_event)
    print(f"Status: {status}")
