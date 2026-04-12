// Test sample for CodeSentinel — intentional bugs, style issues, and security vulnerabilities

var apiKey = "sk-abc123supersecretkey";  // Security: hardcoded secret (HIGH)

// Security: XSS via innerHTML (HIGH)
function renderUserProfile(userData) {
    document.getElementById('profile').innerHTML = userData.bio;
}

// Bug: synchronous XHR blocks the main thread (deprecated)
function fetchData(userId) {
    var url = "https://api.example.com/user/" + userId;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, false);  // false = synchronous
    xhr.send();
    return JSON.parse(xhr.responseText);
}

// Bug: off-by-one error — i <= items.length causes undefined access
function processItems(items) {
    var result = []
    for (var i = 0; i <= items.length; i++) {
        result.push(items[i].toUpperCase())  // TypeError when i === items.length
    }
    return result
}

// Style: missing spaces around operators
var x=1;

// Style: unused variable
const unused_variable = "never used";

// Style: loose equality — should use ===
function badEquals(a, b) {
    return a == b;
}
