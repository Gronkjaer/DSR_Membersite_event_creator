# ------------------------------
# Flask web application
# ------------------------------
# This module serves the web interface for the
# Membersite event creator. It replaces the tkinter GUI
# with a Flask-based web application.
#
# Author: Jonas Groenkjaer Pedersen
# ------------------------------


# ------------------------------
# Packages
# ------------------------------
import sys
import pathlib
import uuid
import datetime
import threading

# Add the src directory to path so backend and autofill_event can be imported.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from flask import Flask, render_template, jsonify, send_from_directory, request  # noqa: E402

import backend  # noqa: E402
from utils import CheckType  # noqa: E402
from autofill_event import create_single_event  # noqa: E402

# ------------------------------
# Flask app initialization
# ------------------------------
app = Flask(__name__)

# Store progress updates per job (keyed by job_id).
# Each entry is a dict with "events" list and "done" flag.
job_progress: dict[str, dict] = {}

job_drivers: dict[str, object] = {}

job_drivers_lock = threading.Lock()


# ------------------------------
# Helper functions
# ------------------------------
def get_folderpath_of_screenshots() -> pathlib.Path:
    """Return the folder path where screenshots are saved."""
    screenshot_dir = pathlib.Path(__file__).resolve().parent / "static" / "screenshots"
    screenshot_dir.mkdir(exist_ok=True)
    return screenshot_dir


def _save_debug_screenshot(driver: object) -> str | None:
    """Save a screenshot for debugging.

    Returns
    -------
    str | None
        The URL of the screenshot or `None` on failure.
    """
    if driver is None:
        return None

    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        img_name = f"debug_screenshot_{current_time}.png"
        img_folder = get_folderpath_of_screenshots()
        img_path = str(img_folder / img_name)
        driver.save_screenshot(img_path)  # pyright: ignore

    except Exception:
        img_path = None

    return img_path


def _delete_old_screenshots(days_old: int = 30) -> None:
    """Delete screenshots older than the specified number of days."""

    # Validate input type.¨
    CheckType.is_int(days_old)

    # Get folder path and current time.
    screenshot_dir = get_folderpath_of_screenshots()
    current_time = datetime.datetime.now()

    # Delete old files.
    for file in screenshot_dir.iterdir():
        if file.is_file() and file.name.startswith("debug_screenshot_") and file.name.endswith(".png"):
            try:
                img_time = datetime.datetime.fromtimestamp(file.stat().st_mtime)
            except ValueError:
                img_time = None
            if img_time is not None:
                age = (current_time - img_time).days
                if age > days_old:
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"Failed to delete the image {file.name}. Received the following error: {e}")

    return None


def extract_user_data_from_web(
    form_data: dict,
) -> dict:
    """Extract user input from web form JSON into backend format.

    Converts the flat JSON from the web form into the
    nested dict structure that backend.validate_user_data()
    expects: {field: {"Use value": bool, "Value": str}}.

    Parameters
    ----------
    form_data : dict
        JSON data from the web form.

    Returns
    -------
    dict
        Structured user data dictionary.
    """
    # Validate input type.
    CheckType.is_dict(form_data)

    # Get the list of field names from backend.
    fields = backend.get_fields()

    # Build the user_data dict in the format backend expects.
    user_data: dict = {}
    repeat_value = form_data.get("repeat", "Ingen gentagelse")
    user_data["Weekly repaet"] = {"Use value": True, "Value": repeat_value}

    for field_name in fields:
        # "Sidste dato" and "Sluttidspunkt" don't have checkboxes.
        if field_name in ["Sidste dato", "Sluttidspunkt"]:
            use_value = None
        else:
            use_value = form_data.get(f"use_{field_name}", True)

        value = form_data.get(field_name, "").strip()
        user_data[field_name] = {"Use value": use_value, "Value": value}

    return user_data


def run_event_creation(
    job_id: str,
    all_events: list[dict],
) -> None:
    """Run Selenium event creation in a background thread.

    Updates job_progress[job_id] with status of each event.

    Parameters
    ----------
    job_id : str
        Unique job identifier for tracking progress.
    all_events : list[dict]
        List of event dictionaries to create.
    """
    # Initialize progress tracking for this job.
    progress = job_progress[job_id]
    driver = None

    for i, event in enumerate(all_events):
        # If a cancel request has been made, stop processing further events.
        if progress.get("cancel_requested"):
            # Close the browser if open.
            if driver is not None:
                try:
                    driver.close()
                    try:
                        driver.quit()
                    except Exception:
                        pass
                except Exception:
                    pass
            # Also remove any stored driver reference for this job.
            try:
                with job_drivers_lock:
                    job_drivers.pop(job_id, None)
            except Exception:
                pass
            # Mark as cancelled and finish.
            progress["cancelled"] = True
            progress["cancelled_count"] = sum(1 for e in progress["events"] if e.get("status") == "success")
            progress["done"] = True
            return

        # Update progress: currently creating event i+1.
        progress["events"].append(
            {
                "index": i + 1,
                "total": len(all_events),
                "status": "creating",
                "message": f"Opretter arrangement {i + 1} af {len(all_events)}...",
            }
        )

        # After the first event, we are already logged in.
        already_logged_in = i > 0

        try:

            def _on_driver_created(drv: object) -> None:
                with job_drivers_lock:
                    job_drivers[job_id] = drv

            driver, response = create_single_event(
                event,
                driver,
                already_logged_in,
                on_driver_created=_on_driver_created,
            )
        except Exception as e:
            # Catch unexpected Selenium errors.
            response = str(e)

        if response == "Succes":
            # Mark event as successfully created.
            progress["events"][-1]["status"] = "success"
            progress["events"][-1]["message"] = f"Arrangement {i + 1} af {len(all_events)} oprettet."

            # Build subset for duplicate detection (returned to frontend).
            start_time = event.get("Start time")
            end_time = event.get("End time")
            progress["events"][-1]["subset"] = {
                "Titel": event.get("Titel", ""),
                "Navn på gruppe": event.get("Navn på gruppe", ""),
                "Start time": start_time.isoformat() if isinstance(start_time, datetime.datetime) else "",
                "End time": end_time.isoformat() if isinstance(end_time, datetime.datetime) else "",
            }

        # If creation failed.
        else:

            # Mark event as failed and stop processing remaining events.
            start_time = event.get("Start time")
            date_str = ""
            if isinstance(start_time, datetime.datetime):
                date_str = start_time.strftime("%d-%m-%Y")
            error_msg = response
            if len(all_events) > 1:
                error_msg += f"\n\nDenne fejl opstod for arrangementet den {date_str}"

            # Save a screenshot for debugging.
            if driver is not None:
                _delete_old_screenshots()
                screenshot_path = _save_debug_screenshot(driver)
                if screenshot_path is not None:
                    link_html = f'<a href="{screenshot_path}" target="_blank">Vis skærmbillede af fejlen</a>'
                    error_msg += f"<br>{link_html}"

            progress["events"][-1]["status"] = "error"
            progress["events"][-1]["message"] = error_msg

            break

    # Close the browser driver if it was opened.
    if driver is not None:
        try:
            driver.close()
        except Exception:
            pass
        # Remove driver reference from global driver store if present.
        try:
            with job_drivers_lock:
                job_drivers.pop(job_id, None)
        except Exception:
            pass

    # Mark the job as done.
    progress["done"] = True


# ------------------------------
# Routes
# ------------------------------
@app.route("/")
def index() -> str:
    """Serve the main page with all three tabs."""
    # Fetch field definitions and options from backend.
    fields = backend.get_fields()
    default_values = backend.get_default_values_that_may_be_used()
    radiobutton_options = backend.get_radiobutton_options()

    return render_template(
        "base.html",
        fields=fields,
        default_values=default_values,
        radiobutton_options=radiobutton_options,
    )


@app.route("/api/create_events", methods=["POST"])
def api_create_events():
    """Validate form data and start event creation.

    Accepts JSON with form field values, validates using
    backend logic, and starts a background thread for
    Selenium event creation.

    Returns
    -------
    JSON
        On validation error: {"status": "error", "message": str}
        On success: {"status": "started", "job_id": str,
                     "event_count": int}
    """
    # Parse JSON body from the request.
    form_data = request.get_json()
    if not form_data:
        return jsonify({"status": "error", "message": "Ingen data modtaget."}), 400

    # Convert web form data to backend format.
    try:
        user_data = extract_user_data_from_web(form_data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    # Validate using backend (no interactive confirm callback for web).
    response = backend.validate_user_data(user_data, confirm=None)
    if response != "Valid":
        return jsonify({"status": "error", "message": response}), 400

    # Apply default values for empty fields.
    user_data = backend.use_default_values_if_not_entered(user_data)

    # Convert numeric string fields to integers.
    user_data = backend.convert_integer_fields(user_data)

    # Convert to a list of event dictionaries.
    all_events = backend.convert_userdata_into_list_of_events(user_data)

    if len(all_events) == 0:
        return jsonify({"status": "error", "message": "Ingen arrangementer at oprette."}), 400

    # Create a unique job ID for tracking progress.
    job_id = str(uuid.uuid4())
    job_progress[job_id] = {
        "events": [],
        "done": False,
        "total": len(all_events),
        "cancel_requested": False,
        "cancelled": False,
    }

    # Start event creation in a background thread.
    thread = threading.Thread(
        target=run_event_creation,
        args=(job_id, all_events),
        daemon=True,
    )
    thread.start()

    return jsonify(
        {
            "status": "started",
            "job_id": job_id,
            "event_count": len(all_events),
        }
    )


@app.route("/api/progress/<job_id>")
def api_progress(job_id: str):
    """Return current progress for a running job.

    Parameters
    ----------
    job_id : str
        The unique job identifier.

    Returns
    -------
    JSON
        {"events": [...], "done": bool}
    """
    # Look up progress for the given job ID.
    progress = job_progress.get(job_id)
    if progress is None:
        return jsonify({"status": "error", "message": "Job ikke fundet."}), 404

    return jsonify(progress)


@app.route("/screenshots/<path:filename>")
def screenshots(filename: str):
    """Serve saved screenshots and page sources for debugging."""
    screenshot_dir = get_folderpath_of_screenshots()
    return send_from_directory(str(screenshot_dir), filename)


@app.route("/api/cancel/<job_id>", methods=["POST"])
def api_cancel(job_id: str):
    """Request cancellation of a running job and close the browser if open."""
    progress = job_progress.get(job_id)
    if progress is None:
        return jsonify({"status": "error", "message": "Job ikke fundet."}), 404

    # Signal cancellation to the background thread.
    progress["cancel_requested"] = True

    # Try to close the driver if available (from global driver store).
    with job_drivers_lock:
        driver = job_drivers.pop(job_id, None)
    if driver is not None:
        try:
            driver.close()  # pyright: ignore
            try:
                driver.quit()  # pyright: ignore
            except Exception:
                pass
        except Exception:
            pass

    # Summarize how many were created so far and mark job done.
    cancelled_count = sum(1 for e in progress.get("events", []) if e.get("status") == "success")
    progress["cancelled"] = True
    progress["cancelled_count"] = cancelled_count
    progress["done"] = True

    return jsonify({"status": "cancelled", "cancelled_count": cancelled_count})


# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
