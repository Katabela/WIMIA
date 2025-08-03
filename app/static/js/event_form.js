function addEventDay() {
  const container = document.getElementById("event-days-container");
  const count = container.querySelectorAll(".day-entry").length + 1;

  const div = document.createElement("div");
  div.className = "mb-3 day-entry";

  const label = document.createElement("label");
  label.className = "form-label w-100";
  label.innerText = `Day ${count}`;

  const group = document.createElement("div");
  group.className = "input-group mb-2";

  const startSpan = document.createElement("span");
  startSpan.className = "input-group-text";
  startSpan.innerText = "Start";

  const startInput = document.createElement("input");
  startInput.type = "datetime-local";
  startInput.name = "event_start_times";
  startInput.className = "form-control";
  startInput.required = true;

  const endSpan = document.createElement("span");
  endSpan.className = "input-group-text";
  endSpan.innerText = "End";

  const endInput = document.createElement("input");
  endInput.type = "datetime-local";
  endInput.name = "event_end_times";
  endInput.className = "form-control";
  endInput.required = true;

  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "btn btn-danger remove-day";
  removeBtn.innerText = "Remove";
  removeBtn.onclick = () => div.remove();

  group.append(startSpan, startInput, endSpan, endInput, removeBtn);
  div.append(label, group);
  container.appendChild(div);
}

// Enable removal of existing days
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".remove-day").forEach((btn) => {
    btn.onclick = () => btn.parentElement.remove();
  });
});

// Add a new coach flight entry
function addFlightEntry() {
  const container = document.getElementById("flight-info-container");

  const entry = document.createElement("div");
  entry.className = "flight-entry mb-4 border rounded p-3";

  entry.innerHTML = `
    <label>Email</label>
    <input type="email" name="flight_email" class="form-control mb-2" list="users-emails" required />

    <label>Name (Optional)</label>
    <input type="text" name="flight_name" class="form-control mb-2" />

    <label>Departure Date & Time</label>
    <input type="datetime-local" name="flight_departure_datetime" class="form-control mb-2" />

    <label>Return Date & Time</label>
    <input type="datetime-local" name="flight_return_datetime" class="form-control mb-2" />

    <label>Airline</label>
    <input type="text" name="flight_airline" class="form-control mb-2" />

    <label>Bag Info</label><br />
    <div class="form-check form-check-inline">
      <input class="form-check-input" type="checkbox" name="flight_bag_info" value="personal" />
      <label class="form-check-label">Personal Item</label>
    </div>
    <div class="form-check form-check-inline">
      <input class="form-check-input" type="checkbox" name="flight_bag_info" value="carry_on" />
      <label class="form-check-label">Carry-On</label>
    </div>
    <div class="form-check form-check-inline">
      <input class="form-check-input" type="checkbox" name="flight_bag_info" value="checked" />
      <label class="form-check-label">Checked Luggage</label>
    </div>

    <label class="mt-2">Confirmation Code</label>
    <input type="text" name="flight_confirmation_code" class="form-control mb-2" />

    <button type="button" class="btn btn-danger remove-flight-entry">Remove</button>
    <hr />
  `;

  // Add remove functionality
  entry.querySelector(".remove-flight-entry").onclick = () => entry.remove();

  container.appendChild(entry);
}

document.addEventListener("click", function (e) {
  if (e.target.classList.contains("remove-flight-entry")) {
    e.target.closest(".flight-entry").remove();
  }
});
