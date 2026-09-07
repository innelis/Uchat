document.addEventListener("DOMContentLoaded", () => {
    const chatMessages = document.getElementById("chat-messages");
    const messageForm = document.getElementById("message-form");
    const messageInput = document.getElementById("message-input");
    const contactSearch = document.getElementById("contact-search");
    const contactList = document.getElementById("contact-list");

    // Scroll chat to bottom on load
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // ---- Send message ----
    if (messageForm && chatMessages) {
        const userId = chatMessages.dataset.userId;

        messageForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const body = messageInput.value.trim();
            if (!body) return;

            messageInput.value = "";

            const formData = new FormData();
            formData.append("body", body);

            try {
                const res = await fetch(`/api/send/${userId}`, {
                    method: "POST",
                    body: formData,
                });
                const data = await res.json();
                if (!res.ok) {
                    console.error(data.error);
                    return;
                }
                appendMessage(data);
                chatMessages.dataset.lastId = data.id;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } catch (err) {
                console.error("Failed to send message", err);
            }
        });

        // ---- Poll for new messages ----
        setInterval(async () => {
            const lastId = chatMessages.dataset.lastId || 0;
            try {
                const res = await fetch(`/api/messages/${userId}?since=${lastId}`);
                const messages = await res.json();
                messages.forEach((m) => {
                    appendMessage(m);
                    chatMessages.dataset.lastId = m.id;
                });
                if (messages.length) {
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            } catch (err) {
                console.error("Polling error", err);
            }
        }, 2500);
    }

    function appendMessage(m) {
        // avoid duplicating a message we already rendered optimistically
        if (document.querySelector(`[data-msg-id="${m.id}"]`)) return;

        const row = document.createElement("div");
        row.className = `message-row ${m.is_mine ? "mine" : "theirs"}`;
        row.setAttribute("data-msg-id", m.id);
        row.innerHTML = `
            <div class="bubble">
                <span class="bubble-text"></span>
                <span class="bubble-time">${m.timestamp}</span>
            </div>
        `;
        row.querySelector(".bubble-text").textContent = m.body; // safe text insert
        chatMessages.appendChild(row);
    }

    // ---- Sidebar search filter ----
    if (contactSearch && contactList) {
        contactSearch.addEventListener("input", () => {
            const query = contactSearch.value.toLowerCase();
            contactList.querySelectorAll(".contact-item[data-name]").forEach((item) => {
                item.style.display = item.dataset.name.includes(query) ? "" : "none";
            });
        });
    }

    // ---- Poll sidebar for unread counts / previews ----
    setInterval(async () => {
        try {
            const res = await fetch("/api/sidebar");
            const data = await res.json();
            data.forEach((entry) => {
                const item = document.querySelector(`.contact-item[data-user-id="${entry.user_id}"]`);
                if (!item) return;
                const preview = item.querySelector("[data-preview]");
                const time = item.querySelector("[data-time]");
                const badge = item.querySelector("[data-badge]");
                if (preview && entry.last_message) preview.textContent = entry.last_message;
                if (time && entry.last_time) time.textContent = entry.last_time;
                if (badge) {
                    if (entry.unread_count > 0 && !item.classList.contains("active")) {
                        badge.textContent = entry.unread_count;
                        badge.style.display = "";
                    } else {
                        badge.style.display = "none";
                    }
                }
            });
        } catch (err) {
            console.error("Sidebar polling error", err);
        }
    }, 4000);
});
