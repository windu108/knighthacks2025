
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
import { getDatabase, ref, push, onValue } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-database.js";

const firebaseConfig = {
    apiKey: "AIzaSyCWyx-mFqHWF9bj4UCMWuBD0A6BOhP-Oq8",
    authDomain: "meet-ebd8a.firebaseapp.com",
    projectId: "meet-ebd8a",
    storageBucket: "meet-ebd8a.firebasestorage.app",
    messagingSenderId: "642169862175",
    appId: "1:642169862175:web:b2a6f6b26a1579486a3d2a",
    measurementId: "G-RQBN1YYX6E"
};

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);
const entriesRef = ref(db, "entries");

document.getElementById("submitBtn").addEventListener("click", () => {
    const location = document.getElementById("locationInput").value;

    const budget = document.getElementById("budgetInput").value;

    const interests = document.getElementById("interestsInput").value;

    const availability = collectAvailability();

    if (location.trim() !== "" && budget.trim() !== "" && interests.trim() !== "") {
        const entry = { location, budget, interests, availability}
        push(entriesRef, entry);
        document.getElementById("locationInput").value = "";
        document.getElementById("budgetInput").value = "";
        document.getElementById("interestsInput").value = "";
    }
    else {

    }
});

/**
* Gathers all selected time slots from the calendar table.
* @returns {Array} An array of objects: [{day: "Mon", time: "8:00 AM"}, ...]
*/
function collectAvailability() {
    const availability = [];
    const table = document.getElementById('calendarTable');
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach((row, rowIndex) => {
        const timeCell = row.querySelector('td:first-child');
        if (!timeCell) return; // Skip if no time cell is found

        const timeSlot = timeCell.textContent;
        const dayCells = row.querySelectorAll('.calendar-cell');

        dayCells.forEach((cell, dayIndex) => {
            if (cell.classList.contains('selected')) {
                // Map day index (0-6) to day name
                const daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
                availability.push({
                    day: daysOfWeek[dayIndex],
                    time: timeSlot
                });
            }
        });
    });
    return availability;
}



onValue(entriesRef, (snapshot) => {
    const list = document.getElementById("messagesList");
    list.innerHTML = "";
    snapshot.forEach((child) => {
        const li = document.createElement("li");
        li.textContent = child.val();
        list.appendChild(li);
    });
});