// Toggle the chatbot visibility
function toggleChatbot() {
  const win = document.getElementById("chatbotWindow");
  const icon = document.querySelector(".chatbot-icon");
  const isOpen = win.style.display === "flex";

  win.style.display = isOpen ? "none" : "flex";
  icon.style.display = isOpen ? "block" : "none";
}

// Send message to the Flask backend
async function sendChat() {
  const input = document.getElementById("chatInput");
  const userText = input.value.trim();
  if (!userText) return;

  const messages = document.getElementById("chatbotMessages");
  messages.innerHTML += `<div class="msg user-msg">${userText}</div>`;
  input.value = "";

  try {
    const res = await fetch("/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userText }),
    });

    const data = await res.json();
    messages.innerHTML += `<div class="msg bot-msg">${data.reply}</div>`;
    messages.scrollTop = messages.scrollHeight;
  } catch (error) {
    messages.innerHTML += `<div class="msg bot-msg">⚠️ Sorry, I couldn't respond right now.</div>`;
    console.error("Fetch error:", error);
  }
}

// Optional: Send on Enter key
document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("chatInput");
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChat();
  });
});
