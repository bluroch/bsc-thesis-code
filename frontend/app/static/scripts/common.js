function logout() {
    fetch('/logout', {
        method: 'POST',
    }).then(response => {
        if (response.ok) {
            window.location.href = '/login';
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}

// Source: https://stackoverflow.com/a/21682946
function stringToColor(string, saturation = 100, lightness = 70) {
    let hash = 0;
    for (let i = 0; i < string.length; i++) {
        hash = string.charCodeAt(i) + ((hash << 5) - hash);
        hash = hash & hash;
    }
    return `hsl(${(hash % 360)}, ${saturation}%, ${lightness}%)`;
}
