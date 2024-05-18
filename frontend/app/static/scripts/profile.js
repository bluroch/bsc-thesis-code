function generateKey() {
    let expirationInput = document.getElementById("expirationDate").value;
    if (expirationInput === "") {
        let errorContainer = document.getElementById("errors");
        errorContainer.classList.remove("d-none");
        errorContainer.innerText = "Please select an expiration date.";
        return;
    }
    let expiry = new Date(Date.parse(expirationInput));
    let now = new Date(Date.now());
    let errorContainer = document.getElementById("errors");
    if (expiry < now) {

        document.getElementById("expirationDate").value = "";
        errorContainer.classList.remove("d-none");
        errorContainer.innerText = "Please select a future date for expiration.";
        return;
    }
    errorContainer.classList.add("d-none");
    let payload = {expiration_date: expiry.toISOString()};
    let apiKey;
    fetch("/generate_key", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        apiKey = data.api_key;
        document.getElementById("copyButton").classList.remove("d-none");
        document.getElementById("apiKeyContainer").innerText = apiKey;
        document.getElementById("generateButton").disabled = true;
    })
    .catch(error => {
        errorContainer.innerText = error.message;
        errorContainer.classList.remove("d-none");
        console.log("Couldn't generate API key: " + error.message);
    });
    document.getElementById("copyButton").classList.remove("d-none");
}

const copyBtnContent = `<i class="bi bi-clipboard me-1"></i>Copy`;
const copyBtnSuccessContent = `<i class="bi bi-clipboard-check me-1"></i>Copied!`;

function copyApiKey() {
    let key = document.getElementById("apiKeyContainer").innerText;
    navigator.clipboard.writeText(key);
    document.getElementById("copyButton").innerText = "Copied!";
    setTimeout(() => {
        document.getElementById("copyButton").innerHTML = copyBtnContent;
    }, 1000);
}

function resetApiKeyGeneration() {
    delete key;
    document.getElementById("apiKeyContainer").innerHTML = `
    <span id="apiKeyContainer">Click on generate...</span>
    <button
      id="copyButton"
      type="button"
      class="btn d-none"
      onclick="copyApiKey()"
    >
    <i class="bi bi-clipboard me-1"></i>Copy
    </button>`;
    document.getElementById("expirationDate").value = "";
    document.getElementById("generateButton").disabled = false;
}