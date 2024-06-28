const messageBar = document.querySelector(".bar-wrapper input");
const sendBtn = document.querySelector(".bar-wrapper button");
const messageBox = document.querySelector(".message-box");

sendBtn.onclick = function () {
    if (messageBar.value.trim().length > 0) {
        const UserTypedMessage = messageBar.value.trim();
        messageBar.value = "";

        let userMessage = `
            <div class="chat message">
                <img src="/static/img/user.png">
                <span>${UserTypedMessage}</span>
            </div>`;

        let botResponse = `
            <div class="chat response">
                <img src="/static/img/book.png">
                <span class="new">...</span>
            </div>`;

        messageBox.insertAdjacentHTML("beforeend", userMessage);

        // Scroll to bottom of message box after inserting user message
        messageBox.scrollTop = messageBox.scrollHeight;

        setTimeout(() => {
            messageBox.insertAdjacentHTML("beforeend", botResponse);

            const requestOptions = {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ user_input: UserTypedMessage })
            };

            fetch('/chat', requestOptions)
                .then(response => response.json())
                .then(data => {
                    const booksResponse = data.response; // Assuming this is the response containing books

                    // Splitting the books response into individual book entries
                    const books = booksResponse.split(/\d+\.\s+/).filter(Boolean);

                    // Creating HTML for the books as lines/bullets
                    let booksHTML = '';
                    books.forEach(book => {
                        booksHTML += `<div>${book.trim()}</div>`;
                    });

                    const ChatBotResponse = document.querySelector(".response .new:last-child");
                    if (ChatBotResponse) {
                        ChatBotResponse.innerHTML = booksHTML;
                        ChatBotResponse.classList.remove("new");

                        // Scroll to bottom of message box after inserting bot response
                        messageBox.scrollTop = messageBox.scrollHeight;
                    }
                })
                .catch(error => {
                    const ChatBotResponse = document.querySelector(".response .new:last-child");
                    if (ChatBotResponse) {
                        ChatBotResponse.innerHTML = "Oops! An error occurred. Please try again.";
                        ChatBotResponse.classList.remove("new");

                        // Scroll to bottom of message box after inserting error message
                        messageBox.scrollTop = messageBox.scrollHeight;
                    }
                    console.error('Error:', error);
                });
        }, 100);
    }
};
