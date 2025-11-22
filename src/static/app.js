document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Clear existing select options (keep placeholder)
      activitySelect.querySelectorAll("option:not([value=''])").forEach(o => o.remove());

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;


        // Build participants DOM
        const participants = Array.isArray(details.participants) ? details.participants : [];
        const participantsWrap = document.createElement('div');
        participantsWrap.className = 'participants';

        const participantsTitle = document.createElement('h5');
        participantsTitle.textContent = 'Participants';
        participantsWrap.appendChild(participantsTitle);

        if (participants.length === 0) {
          const noP = document.createElement('p');
          noP.className = 'no-participants';
          noP.textContent = 'No participants yet';
          participantsWrap.appendChild(noP);
        } else {
          const ul = document.createElement('ul');
          ul.className = 'participants-list';

          participants.forEach(p => {
            const li = document.createElement('li');

            const badge = document.createElement('span');
            badge.className = 'participant-badge';
            badge.textContent = p;

            // delete button (simple × icon)
            const removeBtn = document.createElement('button');
            removeBtn.className = 'participant-remove';
            removeBtn.setAttribute('aria-label', `Unregister ${p}`);
            removeBtn.textContent = '×';

            // Attach click handler to remove participant
            removeBtn.addEventListener('click', async () => {
              if (!confirm(`Unregister ${p} from ${name}?`)) return;
              try {
                const res = await fetch(`/activities/${encodeURIComponent(name)}/participants?email=${encodeURIComponent(p)}`, { method: 'DELETE' });
                const data = await res.json();
                if (res.ok) {
                  // refresh activities list
                  await fetchActivities();
                } else {
                  messageDiv.textContent = data.detail || data.message || 'Failed to unregister';
                  messageDiv.className = 'error';
                  messageDiv.classList.remove('hidden');
                  setTimeout(() => messageDiv.classList.add('hidden'), 5000);
                }
              } catch (err) {
                console.error('Error unregistering:', err);
                messageDiv.textContent = 'Failed to unregister. Please try again.';
                messageDiv.className = 'error';
                messageDiv.classList.remove('hidden');
                setTimeout(() => messageDiv.classList.add('hidden'), 5000);
              }
            });

            li.appendChild(badge);
            li.appendChild(removeBtn);
            ul.appendChild(li);
          });

          participantsWrap.appendChild(ul);
        }

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
        `;

        activityCard.appendChild(participantsWrap);

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "message success";
        signupForm.reset();

        // Refresh activities so the new participant appears immediately
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "message error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
