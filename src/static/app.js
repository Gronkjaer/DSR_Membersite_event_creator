// Main JavaScript file for the Membersite event creator web app.
// Handles localStorage persistence, form validation, and API calls.

// localStorage key prefixes to avoid conflicts with other apps.
const STORAGE_KEY_INPUTS = "membersite_user_inputs";
const STORAGE_KEY_PREVIOUS = "membersite_previous_events";

// Debounce timer for auto-saving form data.
let saveTimer = null;


// ------------------------------
// localStorage functions
// ------------------------------

/**
 * Save all form field values and checkbox states to localStorage.
 * Called on every input change (debounced to prevent excessive writes).
 */
function saveFormToLocalStorage() {
    const data = {};

    // Collect all text/password input fields.
    document.querySelectorAll(".field-input").forEach(function (input) {
        data[input.name] = input.value;
    });

    // Collect all checkbox states.
    document.querySelectorAll(".field-checkbox").forEach(function (checkbox) {
        data[checkbox.name] = checkbox.checked;
    });

    // Collect radio button selection.
    const selectedRadio = document.querySelector('input[name="repeat"]:checked');
    if (selectedRadio) {
        data["repeat"] = selectedRadio.value;
    }

    // Write to localStorage as JSON string.
    localStorage.setItem(STORAGE_KEY_INPUTS, JSON.stringify(data));
}

/**
 * Load previously saved form values from localStorage and populate the form.
 * Called once when the page loads.
 */
function loadFormFromLocalStorage() {
    const stored = localStorage.getItem(STORAGE_KEY_INPUTS);
    if (!stored) {
        return; // No saved data exists.
    }

    let data;
    try {
        data = JSON.parse(stored);
    } catch (e) {
        return; // Invalid JSON, ignore.
    }

    // Restore text/password input values, using flatpickr API for date pickers.
    document.querySelectorAll(".field-input").forEach(function (input) {
        if (data[input.name] !== undefined) {
            // Use flatpickr's setDate if this input has been initialised as a date picker.
            if (input._flatpickr) {
                input._flatpickr.setDate(data[input.name], false);
            } else {
                input.value = data[input.name];
            }
        }
    });

    // Restore checkbox states.
    document.querySelectorAll(".field-checkbox").forEach(function (checkbox) {
        if (data[checkbox.name] !== undefined) {
            checkbox.checked = data[checkbox.name];
        }
    });

    // Restore radio button selection.
    if (data["repeat"]) {
        const radio = document.querySelector(
            'input[name="repeat"][value="' + data["repeat"] + '"]'
        );
        if (radio) {
            radio.checked = true;
        }
    }
}

/**
 * Load previous events from localStorage.
 * Returns an array of event objects (or empty array if none saved).
 */
function loadPreviousEvents() {
    const stored = localStorage.getItem(STORAGE_KEY_PREVIOUS);
    if (!stored) {
        return [];
    }
    try {
        return JSON.parse(stored);
    } catch (e) {
        return [];
    }
}

/**
 * Save previous events to localStorage.
 * @param {Array} events - Array of event subset objects.
 */
function savePreviousEvents(events) {
    localStorage.setItem(STORAGE_KEY_PREVIOUS, JSON.stringify(events));
}

/**
 * Debounced save: waits 500ms after last change before saving.
 * Prevents excessive localStorage writes during rapid typing.
 */
function debouncedSave() {
    if (saveTimer) {
        clearTimeout(saveTimer);
    }
    saveTimer = setTimeout(saveFormToLocalStorage, 500);
}


// ------------------------------
// Form data collection
// ------------------------------

/**
 * Collect all form field values into a flat JSON object for the API.
 * Includes field values, checkbox states, and radio selection.
 * @returns {Object} Form data ready for submission.
 */
function collectFormData() {
    const data = {};

    // Collect all text/password/textarea input fields.
    document.querySelectorAll(".field-input").forEach(function (input) {
        data[input.name] = input.value.trim();
    });

    // Collect all checkbox states (true/false).
    document.querySelectorAll(".field-checkbox").forEach(function (checkbox) {
        data[checkbox.name] = checkbox.checked;
    });

    // Collect radio button selection.
    const selectedRadio = document.querySelector('input[name="repeat"]:checked');
    if (selectedRadio) {
        data["repeat"] = selectedRadio.value;
    }

    return data;
}


/**
 * Normalize a time input: if exactly 4 digits are entered without a colon,
 * insert the colon after the 2nd digit (e.g. "1000" → "10:00").
 * @param {HTMLInputElement} input - The time input element to normalize.
 */
function normalizeTimeInput(input) {
    const val = input.value.trim();
    // Match exactly four digits with no separators and reformat as HH:MM.
    if (/^\d{4}$/.test(val)) {
        input.value = val.substring(0, 2) + ":" + val.substring(2);
    }
}


// ------------------------------
// Client-side validation
// ------------------------------

/**
 * Clear all validation error messages from the form.
 */
function clearValidationErrors() {
    document.querySelectorAll(".validation-error").forEach(function (el) {
        el.remove();
    });
    // Remove red border from previously invalid fields.
    document.querySelectorAll(".is-invalid").forEach(function (el) {
        el.classList.remove("is-invalid");
    });
}

/**
 * Show a validation error message next to a specific field.
 * @param {string} fieldName - The name attribute of the field input.
 * @param {string} message - The error message to display.
 */
function showFieldError(fieldName, message) {
    const input = document.querySelector('[name="' + fieldName + '"]');
    if (!input) return;

    // Add red border to the field.
    input.classList.add("is-invalid");

    // Create error message element.
    const errorDiv = document.createElement("div");
    errorDiv.className = "validation-error text-danger small mt-1";
    errorDiv.textContent = message;

    // Insert error after the field's parent row.
    const row = input.closest(".row");
    if (row) {
        row.appendChild(errorDiv);
    }
}

/**
 * Run client-side validation on the form data.
 * Returns true if valid, false if errors were found.
 * @returns {boolean} Whether the form is valid.
 */
function validateForm() {
    clearValidationErrors();
    const data = collectFormData();
    let isValid = true;

    // Check required fields (only if their checkbox is checked).
    const requiredFields = {
        "Email": "Email",
        "Adgangskode": "Adgangskode",
        "Navn på gruppe": "Navn på gruppe",
        "Navn på skabelon": "Navn på skabelon",
        "Første dato": "Dato(er)",
        "Starttidspunkt": "Starttidspunkt",
        "Sluttidspunkt": "Sluttidspunkt",
        "Titel": "Titel"
    };

    for (const [fieldName, displayName] of Object.entries(requiredFields)) {
        const checkboxName = "use_" + fieldName;
        // If checkbox is checked (or doesn't exist), field is required.
        if (data[checkboxName] !== false) {
            if (!data[fieldName] || data[fieldName] === "") {
                showFieldError(fieldName, displayName + " er påkrævet.");
                isValid = false;
            }
        }
    }

    // Validate email format.
    if (data["use_Email"] !== false && data["Email"] && !data["Email"].includes("@")) {
        showFieldError("Email", "Ugyldig email.");
        isValid = false;
    }

    // Validate date format (DD-MM-YYYY).
    const datePattern = /^\d{2}-\d{2}-\d{4}$/;
    if (data["Første dato"] && !datePattern.test(data["Første dato"])) {
        showFieldError("Første dato", "Ugyldigt format. Brug DD-MM-YYYY.");
        isValid = false;
    }
    if (data["Sidste dato"] && data["Sidste dato"] !== "" && !datePattern.test(data["Sidste dato"])) {
        showFieldError("Sidste dato", "Ugyldigt format. Brug DD-MM-YYYY.");
        isValid = false;
    }

    // Validate time format (HH:MM).
    const timePattern = /^\d{2}:\d{2}$/;
    if (data["Starttidspunkt"] && !timePattern.test(data["Starttidspunkt"])) {
        showFieldError("Starttidspunkt", "Ugyldigt format. Brug HH:MM.");
        isValid = false;
    }
    if (data["Sluttidspunkt"] && !timePattern.test(data["Sluttidspunkt"])) {
        showFieldError("Sluttidspunkt", "Ugyldigt format. Brug HH:MM.");
        isValid = false;
    }

    // Validate repeat vs end date consistency.
    if (data["repeat"] === "Ingen gentagelse" && data["Sidste dato"] !== "") {
        showFieldError("Sidste dato", "Eftersom arrangementet ikke gentages, skal du ikke indtaste en slutdato.");
        isValid = false;
    }
    if (data["repeat"] !== "Ingen gentagelse" && (!data["Sidste dato"] || data["Sidste dato"] === "")) {
        showFieldError("Sidste dato", "Eftersom arrangementet gentages, skal du indtaste en slutdato.");
        isValid = false;
    }

    return isValid;
}


// ------------------------------
// Duplicate detection
// ------------------------------

/**
 * Check if any events in the list match previously created events.
 * Shows a confirmation modal if duplicates are found.
 * @param {Object} formData - The form data to submit.
 * @returns {Promise<boolean>} Whether to proceed with creation.
 */
function checkForDuplicates(formData) {
    const previousEvents = loadPreviousEvents();
    if (previousEvents.length === 0) {
        return Promise.resolve(true); // No previous events, no duplicates.
    }

    // Check if the event title and date combo matches any previous event.
    const firstDate = formData["Første dato"];
    const titel = formData["Titel"];
    const gruppe = formData["Navn på gruppe"];

    for (const prev of previousEvents) {
        // Compare title, group, and start date.
        if (prev["Titel"] === titel && prev["Navn på gruppe"] === gruppe) {
            const prevDate = prev["Start time"] ? prev["Start time"].substring(0, 10) : "";
            // Parse DD-MM-YYYY to YYYY-MM-DD for comparison.
            let formattedDate = "";
            if (firstDate && firstDate.length === 10) {
                formattedDate = firstDate.substring(6) + "-" + firstDate.substring(3, 5) + "-" + firstDate.substring(0, 2);
            }
            if (prevDate === formattedDate) {
                // Show duplicate confirmation modal.
                return new Promise(function (resolve) {
                    const modal = new bootstrap.Modal(document.getElementById("duplicateModal"));
                    document.getElementById("duplicateMessage").textContent =
                        "Arrangementet for " + firstDate + " er blevet oprettet tidligere. " +
                        "Inden du fortsætter, bør du dobbelttjekke at arrangementet " +
                        "ikke findes i forvejen på Membersite. Vil du forsat oprette arrangementet?";

                    // Handle confirm button click.
                    const confirmBtn = document.getElementById("duplicateConfirm");
                    const handler = function () {
                        confirmBtn.removeEventListener("click", handler);
                        modal.hide();
                        resolve(true);
                    };
                    confirmBtn.addEventListener("click", handler);

                    // Handle cancel/dismiss.
                    document.getElementById("duplicateModal").addEventListener("hidden.bs.modal", function onHidden() {
                        document.getElementById("duplicateModal").removeEventListener("hidden.bs.modal", onHidden);
                        resolve(false); // User dismissed the modal.
                    }, { once: true });

                    modal.show();
                });
            }
        }
    }

    return Promise.resolve(true); // No duplicates found.
}


// ------------------------------
// Progress tracking
// ------------------------------

/**
 * Poll the backend for progress updates on a running job.
 * Updates the progress modal with status messages.
 * @param {string} jobId - The job ID returned by the API.
 */
function pollProgress(jobId) {
    const messagesDiv = document.getElementById("progressMessages");
    const footer = document.getElementById("progressFooter");
    const activeFooter = document.getElementById("progressActiveFooter");

    const interval = setInterval(function () {
        fetch("/api/progress/" + jobId)
            .then(function (res) { return res.json(); })
            .then(function (data) {
                // Update the progress messages display.
                let html = "";
                for (const event of data.events) {
                    let icon = "";
                    let cls = "";
                    if (event.status === "creating") {
                        icon = "⏳";
                        cls = "text-primary";
                    } else if (event.status === "success") {
                        icon = "✅";
                        cls = "text-success";
                    } else if (event.status === "error") {
                        icon = "❌";
                        cls = "text-danger";
                    }
                    html += '<p class="' + cls + ' mb-1">' + icon + " " + event.message + "</p>";
                }
                messagesDiv.innerHTML = html;

                // Show cancel button while any event is actively being created.
                if (activeFooter) {
                    const hasCreating = Array.isArray(data.events) && data.events.some(function (e) { return e && e.status === "creating"; });
                    const cancelBtn = document.getElementById("cancelCreateBtn");
                    if (hasCreating) {
                        activeFooter.style.display = "flex";
                        if (cancelBtn) cancelBtn.disabled = false;
                    } else {
                        activeFooter.style.display = "none";
                        if (cancelBtn) cancelBtn.disabled = true;
                    }
                }

                // If job was cancelled, stop polling and show cancelled summary.
                if (data.cancelled) {
                    clearInterval(interval);
                    if (activeFooter) activeFooter.style.display = "none";
                    footer.style.display = "block";

                    // Save any successful events to localStorage before showing message.
                    const previousEvents = loadPreviousEvents();
                    for (const event of data.events) {
                        if (event.status === "success" && event.subset) {
                            previousEvents.push(event.subset);
                        }
                    }
                    savePreviousEvents(previousEvents);

                    const cancelledCount = data.cancelled_count || data.events.filter(function (e) { return e.status === "success"; }).length;
                    const totalCount = data.total || data.events.length;
                    messagesDiv.innerHTML += '<p class="text-danger fw-bold mt-2">Afbrudt. ' + cancelledCount + ' ud af ' + totalCount + ' arrangementer blev oprettet.</p>';
                    return;
                }

                // If job is done, stop polling and show close button.
                if (data.done) {
                    clearInterval(interval);
                    if (activeFooter) activeFooter.style.display = "none";
                    footer.style.display = "block";

                    // Save successfully created events to localStorage.
                    const previousEvents = loadPreviousEvents();
                    for (const event of data.events) {
                        if (event.status === "success" && event.subset) {
                            previousEvents.push(event.subset);
                        }
                    }
                    savePreviousEvents(previousEvents);

                    // Show final summary.
                    const successCount = data.events.filter(function (e) { return e.status === "success"; }).length;
                    const totalCount = data.total || data.events.length;
                    if (successCount === totalCount) {
                        if (totalCount === 1) {
                            html += '<p class="text-success fw-bold mt-2">Arrangementet blev oprettet.</p>';
                        } else {
                            html += '<p class="text-success fw-bold mt-2">Alle ' + totalCount + ' arrangementer blev oprettet.</p>';
                        }
                    } else {
                        html += '<p class="text-danger fw-bold mt-2">' + successCount + ' af ' + totalCount + ' arrangementer blev oprettet.</p>';
                    }
                    messagesDiv.innerHTML = html;
                }
            })
            .catch(function (err) {
                clearInterval(interval);
                messagesDiv.innerHTML = '<p class="text-danger">Fejl ved hentning af status: ' + err.message + "</p>";
                footer.style.display = "block";
            });
    }, 1500); // Poll every 1.5 seconds.
}


// ------------------------------
// Form submission
// ------------------------------

/**
 * Handle the "Opret arrangement" button click.
 * Validates form, checks for duplicates, submits to API,
 * and shows progress feedback.
 */
async function handleCreateEvent() {
    // Step 1: Client-side validation.
    if (!validateForm()) {
        return;
    }

    // Step 2: Collect form data.
    const formData = collectFormData();

    // Step 3: Save form data to localStorage.
    saveFormToLocalStorage();

    // Step 4: Check for duplicate events.
    const proceed = await checkForDuplicates(formData);
    if (!proceed) {
        return;
    }

    // Step 5: Submit to backend API.
    const createBtn = document.getElementById("createEventBtn");
    createBtn.disabled = true;
    createBtn.textContent = "Opretter...";

    try {
        const response = await fetch("/api/create_events", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData),
        });

        const result = await response.json();

        if (result.status === "error") {
            // Show validation error from backend.
            alert(result.message);
            createBtn.disabled = false;
            createBtn.textContent = "Opret arrangement";
            return;
        }

        // Step 6: Show progress modal and start polling.
        document.getElementById("progressMessages").innerHTML =
            '<p class="text-primary">⏳ Starter oprettelse af ' + result.event_count + ' arrangement(er)...</p>';
        document.getElementById("progressFooter").style.display = "none";
        // Show the active footer (cancel button) while job runs.
        const activeFooter = document.getElementById("progressActiveFooter");
        if (activeFooter) activeFooter.style.display = "flex";

        // Attach cancel handler.
        const cancelBtn = document.getElementById("cancelCreateBtn");
        if (cancelBtn) {
            cancelBtn.disabled = false;
            cancelBtn.onclick = async function () {
                cancelBtn.disabled = true;
                try {
                    await fetch('/api/cancel/' + result.job_id, { method: 'POST' });
                } catch (e) {
                    console.error('Cancel request failed', e);
                }
            };
        }

        const progressModal = new bootstrap.Modal(document.getElementById("progressModal"), {backdrop: 'static', keyboard: false});
        progressModal.show();

        // Start polling for progress updates.
        pollProgress(result.job_id);

        // Re-enable button when modal is closed.
        document.getElementById("progressModal").addEventListener("hidden.bs.modal", function onHidden() {
            document.getElementById("progressModal").removeEventListener("hidden.bs.modal", onHidden);
            createBtn.disabled = false;
            createBtn.textContent = "Opret arrangement";
        }, { once: true });

    } catch (err) {
        // Network or server error.
        alert("Der opstod en fejl: " + err.message + "\nPrøv igen.");
        createBtn.disabled = false;
        createBtn.textContent = "Opret arrangement";
    }
}


// ------------------------------
// Initialization
// ------------------------------

document.addEventListener("DOMContentLoaded", function () {
    // Initialize Bootstrap tooltips on all elements with data-bs-toggle="tooltip".
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function (el) {
        new bootstrap.Tooltip(el);
    });

    // Initialize flatpickr date pickers (must run before loadFormFromLocalStorage).
    document.querySelectorAll(".date-picker").forEach(function (el) {
        flatpickr(el, {
            dateFormat: "d-m-Y",  // Output format: DD-MM-YYYY
            allowInput: true,      // Allow manual text entry in addition to the calendar
            locale: "da",          // Danish calendar labels
        });
    });

    // Load saved form data from localStorage.
    loadFormFromLocalStorage();

    // Ensure the active progress footer (cancel button) is hidden initially.
    const activeFooter = document.getElementById("progressActiveFooter");
    if (activeFooter) {
        activeFooter.style.display = "none";
        const cancelBtnInit = document.getElementById("cancelCreateBtn");
        if (cancelBtnInit) cancelBtnInit.disabled = true;
    }

    // Normalize time fields (e.g. "1000" → "10:00") when the user leaves the field.
    document.querySelectorAll(".time-input").forEach(function (el) {
        el.addEventListener("blur", function () { normalizeTimeInput(el); });
    });

    // Toggle password visibility for the Adgangskode field.
    const toggleBtn = document.getElementById("togglePassword");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            const passwordInput = document.getElementById("field_Adgangskode");
            const eyeIcon = document.getElementById("eyeIcon");
            const eyeSlashIcon = document.getElementById("eyeSlashIcon");
            // Switch between masked and plain-text display.
            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                eyeIcon.style.display = "none";
                eyeSlashIcon.style.display = "";
            } else {
                passwordInput.type = "password";
                eyeIcon.style.display = "";
                eyeSlashIcon.style.display = "none";
            }
        });
    }

    // Attach debounced save to all input, checkbox, and radio changes.
    document.querySelectorAll(".field-input").forEach(function (input) {
        input.addEventListener("input", debouncedSave);
    });
    document.querySelectorAll(".field-checkbox").forEach(function (checkbox) {
        checkbox.addEventListener("change", debouncedSave);
    });
    document.querySelectorAll('input[name="repeat"]').forEach(function (radio) {
        radio.addEventListener("change", debouncedSave);
    });

    // Attach click handler to the "Create event" button.
    const createBtn = document.getElementById("createEventBtn");
    if (createBtn) {
        createBtn.addEventListener("click", handleCreateEvent);
    }
});
