document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("gbj-input");
    const chatBox = document.getElementById("chat-box");
  
    input.addEventListener("keydown", async (e) => {
      if (e.key === "Enter") {
        const userMsg = input.value;
        chatBox.innerHTML += `<div>> ${userMsg}</div>`;
        input.value = "";
  
        const res = await fetch("/gbj/respond", {
          method: "POST",
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userMsg })
        });
        const data = await res.json();
        chatBox.innerHTML += `<div>${data.response}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
      }
    });
  });
  